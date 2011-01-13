"""
"""
import os
import re
import sys

import oursql
from twisted.python import usage
import yaml


ROOT = os.path.abspath(os.path.dirname(__file__))


def executeBatch(cursor, sql,
                  regex=r"(?mx) ([^';]* (?:'[^']*'[^';]*)*)", 
                  comment_regex=r"(?mx) (?:^\s*$)|(?:--.*$)"):
    """
    Takes a SQL file and executes it as many separate statements.

    This function is taken from South, 
    http://south.aeracode.org/browser/south/db/generic.py
    """
    # First, strip comments
    sql = "\n".join([x.strip().replace("%", "%%") for x in re.split(comment_regex, sql) if x.strip()])
    # Now execute each statement
    for st in re.split(regex, sql)[1:][::2]:
        cursor.execute(st)


class DatabaseMigrator(object):
    """
    """

    getVersionSql = """SELECT max(version) FROM migration_info;"""
    createDatabaseSql = """CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8;"""
    useDatabaseSql = """USE %s;"""
    createMigrationTableSql = """CREATE TABLE IF NOT EXISTS migration_info (
 migrationId INT NOT NULL AUTO_INCREMENT,
 version INT NOT NULL,
 name VARCHAR(255) NULL,
 PRIMARY KEY (migrationId))
ENGINE = InnoDB;"""
    
    def __init__(self, indexFilepath, migrationDirectory=None,
                 index=None):
        self.connection = None
        if not migrationDirectory:
            self.migrationDirectory = os.path.dirname(indexFilepath)
        else:
            self.migrationDirectory = migrationDirectory
        if not index:
            self.index = yaml.load(open(indexFilepath, "r").read())
        else:
            self.index = index
        self.migrations = []
        for migration in self.index["migrations"]:
            realPath = os.path.join(self.migrationDirectory, migration)
            if os.path.exists(realPath):
                self.migrations.append(migration)
            else:
                raise ValueError("Missing Migration File")
        self.migrations = self.index["migrations"]

    def connect(self, host, port, user, password, db):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.connection = oursql.connect(host=host, user=user,
                                         passwd=password, port=port)
        cursor = self.connection.cursor()
        cursor.execute(self.createDatabaseSql % (self.db,))
        cursor.close()

    def howToMigrate(self, fromVersion, toVersion=None):
        if toVersion:
            return self.migrations[fromVersion:toVersion]
        else:
            return self.migrations[fromVersion:]

    def getVersion(self, cursor=None):
        if not cursor:
            cursor = self.connection.cursor()
        try:
            cursor.execute(self.useDatabaseSql % (self.db,))
            cursor.execute(self.getVersionSql)
            results = cursor.fetchall()
            versionNumber = results[0][0]
        except oursql.ProgrammingError:
            print "Unable to determine version of this database!"
            versionNumber = None
        else:
            if cursor:
                cursor.close()
        return versionNumber

    def installMigrationInfo(self):
        cursor = self.connection.cursor()
        cursor.execute(self.useDatabaseSql % (self.db,))
        cursor.execute(self.createMigrationTableSql)
        cursor.close()

    def runSql(self, migrationName, version):
        sys.stdout.write("Running migration %s to version %s: ..."%(migrationName, version))
        sqlPath = os.path.join(self.migrationDirectory, migrationName)
        sql = open(sqlPath, "r").read()
        try:
            cursor = self.connection.cursor()
            cursor.execute(self.useDatabaseSql % (self.db,))
            executeBatch(cursor, sql)
            cursor.execute("INSERT INTO migration_info (version, name) VALUES (?, ?);",
                            (version, migrationName))
        except:
            print "\n"
            self.connection.rollback()
            raise
        else:
            self.connection.commit()
        sys.stdout.write("\r")
        sys.stdout.flush()
        sys.stdout.write("Running migration %s to version %s: SUCCESS!\n"%(migrationName, version))
        
    def migrate(self):
        version = self.getVersion()
        migrations = self.howToMigrate(version)
        applied = []
        if version is None:
            version = 0
        for migration in migrations:
            version += 1
            self.runSql(migration, version)
            applied.append(migration)
        if len(migrations) == 0:
            print "Database is already up to date at version: %s"%(version,)
        return applied


__usage__ = """usage: %prog [options] migrations_directory databasename
"""
__version__ = "1.0"


class Options(usage.Options):
    optParameters = [["host", "h", "localhost", "Hostname of database server"],
                     ["port", "r", 3306, "Port of database server", int],
                     ["user", "u", "root", "Username to use when connecting to database"],
                     ["password", "p", "password", "Password to use when connection to the database"]]

    def parseArgs(self, migrationDirectory, databaseName):
        self["migrationDirectory"] = migrationDirectory
        self["databaseName"] = databaseName


class MigrateOptions(Options):
    """Currently this is just here to define the subcommand."""


class ListOptions(Options):
    """Currently this is just here to define the subcommand."""


class GooseOptions(usage.Options):
    subCommands = [["migrate", None, MigrateOptions, "Apply any outstanding migrations to the database."],
                   ["list", None, ListOptions, "List all applied and outstanding migrations"]]

    defaultSubCommand = "migrate"



def migrate(migrationDirectory, host, port, username, password, databasename):
    indexFilepath = os.path.join(migrationDirectory, "index.yaml")
    migrator = DatabaseMigrator(indexFilepath)
    migrator.connect(host, int(port), username, password, databasename)
    migrator.installMigrationInfo()
    migrator.migrate()
    

def listMigrations(migrationDirectory, host, port, username, password, databasename):
    indexFilepath = os.path.join(migrationDirectory, "index.yaml")
    migrator = DatabaseMigrator(indexFilepath)
    migrator.connect(host, int(port), username, password, databasename)
    dbVersion = migrator.getVersion()
    print "Applied(*)  VersionNumber  MigrationName"
    for i, migration in enumerate(migrator.migrations):
        migrationVersion = i+1
        if migrationVersion <= dbVersion:
            print "%-10s  %-13s  %s"%("Y", migrationVersion, migration)
        else:
            print "%-10s  %-13s  %s"%("N ", migrationVersion, migration)
        

def main():
    options = GooseOptions()
    options.parseOptions()
    if options.subCommand == "migrate":
        migrate(options.subOptions["migrationDirectory"],
                options.subOptions["host"],
                options.subOptions["port"],
                options.subOptions["user"],
                options.subOptions["password"],
                options.subOptions["databaseName"])
    elif options.subCommand == "list":
        listMigrations(options.subOptions["migrationDirectory"],
                       options.subOptions["host"],
                       options.subOptions["port"],
                       options.subOptions["user"],
                       options.subOptions["password"],
                       options.subOptions["databaseName"])
        
