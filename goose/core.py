"""goose.py

A configuration driven schema migration tool.

Rather than figuring out what migrations to apply based
on subversion revisions or filename conventions (migration_001.sql, 001_migration.sql, etc) it is determined by a simple configuration file in the YAML format.

"""
import argparse # this isn't a stdlib import yet, but it will be in 2.7
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    """
    Unable to import yaml so only json formatted
    index files will work.
    """


from goose import models


ROOT = os.path.abspath(os.path.dirname(__file__))


def executeBatch(cursor, sql,
                 regex=r"(?mx) ([^';]* (?:'[^']*'[^';]*)*)",
                 comment_regex=r"(?mx) (?:^\s*$)|(?:--.*$)"):
    """
    Takes a SQL file and executes it as many separate statements.

    TODO: replace regexes with something easier to grok and extend.

    """
    # First, strip comments
    sql = "\n".join([x.strip().replace("%", "%%") for x in re.split(comment_regex, sql) if x.strip()])

    # Stored procedures don't work with the above regex because many of them are
    # made up multiple sql statements each delimited with a single ;
    # where the regexes assume each statement delimited by a ; is a complete
    # statement to send to mysql and execute.
    #
    # Here i'm simply checking for the delimiter statements (which seem to be
    # mysql-only) and then using them as markers to start accumulating statements.
    # So the first delimiter is the signal to start accumulating
    # and the second delimiter is the signal to combine them into
    # single sql compound statement and send it to mysql.

    in_proc = False
    statements = []

    for st in re.split(regex, sql)[1:][::2]:
        if st.strip().lower().startswith("delimiter"):
            in_proc = not in_proc
            if statements and not in_proc:
                procedure = ";".join(statements)
                statements = []
                cursor.execute(procedure)
            # skip the delimiter line
            continue

        if in_proc:
            statements.append(st)
        else:
            cursor.execute(st)


def extension(path):
    name, ext = os.path.splitext(path)
    ext = ext.lower()
    return ext


class DatabaseMigrator(object):
    """
    """

    def __init__(self, indexFilepath,
                 index=None):
        self.connection = None
        self.migrationDirectory = os.path.dirname(indexFilepath)
        if not index:
            ext = extension(indexFilepath)
            if ext == ".yaml":
                self.index = yaml.load(open(indexFilepath, "r").read())
            elif ext == ".json":
                self.index = json.loads(open(indexFilepath, "r").read())
            else:
                raise ValueError("Unsupported index file format: %s\n"
                                 "Please use 'json' or 'yaml'."%(ext,))
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

    def connect(self, dsn):
        self.dsn = dsn
        self.session = models.connect(self.dsn)

    def migrationsApplied(self):
        return self.session.query(models.Migration).all()

    def howToMigrate(self, fromVersion, toVersion=None):
        """Given a starting version and an ending version
        returns filenames of all the migrations in that range, exclusive.

        e.g.: [fromVersion, toVersion)
        """
        # slice notation [start:end:step]
        # by adding a step of 1 we make a slice from 0:0 be empty
        # rather than containing the whole list.
        if toVersion is not None:
            return self.migrations[fromVersion:toVersion:1]
        else:
            return self.migrations[fromVersion::1]

    def getVersion(self, session=None):
        if session is None:
            session = self.session
        versionNumber = None
        try:
            versionNumber = session.query(
                models.max(models.Migration.version)).scalar()
        except models.OperationalError:
            raise ValueError("Unable to determine version of this database!\n"
                             "Either database %s does not exist or migration_info table is missing."%(self.dsn,))
        print "versionNumber:", versionNumber
        return versionNumber

    def runSql(self, migrationName, version):
        """
        Given a migration name and version lookup the sql file and run it.
        """
        sys.stdout.write("Running migration %s to version %s: ..."%(migrationName, version))
        sqlPath = os.path.join(self.migrationDirectory, migrationName)
        sql = open(sqlPath, "r").read()
        try:
            if self.session.is_active:
                print "session is active"
                self.session.commit()
            self.session.begin()
            executeBatch(self.session, sql)
            self.session.add(models.Migration(version, migrationName))
        except:
            print "\n"
            self.session.rollback()
            raise
        else:
            self.session.commit()
        sys.stdout.write("\r")
        sys.stdout.flush()
        sys.stdout.write("Running migration %s to version %s: SUCCESS!\n"%(migrationName, version))

    def migrate(self, fromVersion=None, toVersion=None, selectedMigrations=None):
        if fromVersion is None:
            version = self.getVersion()
            fromVersion = version if version is not None else 0
        if selectedMigrations is not None:
            migrations = [self.migrations[i] for i in selectedMigrations]
        else:
            print "fromVersion, toVersion:", fromVersion, toVersion
            migrations = self.howToMigrate(fromVersion, toVersion)
        #import pdb; pdb.set_trace()
        applied = []
        version = fromVersion
        for migration in migrations:
            version += 1
            self.runSql(migration, version)
            applied.append(migration)
        if len(migrations) == 0:
            print "Database is already up to date at version: %s"%(version,)
        return applied


__version__ = "1.0"

__examples__ = """
"""

parser = argparse.ArgumentParser(
    description="simple configuration driven migration tool",
    #epilog=__examples__
    )
parser.add_argument('--version', action='version', version='%%(prog)s %s'%(__version__,))
parser.add_argument("-d", "--dsn", dest="dsn", metavar="DSN", type=str,
                    help="data source name (postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...])")
parser.add_argument("-m", "--migrations", dest="migrationDirectory", metavar="MIGRATION_DIR", type=str,
                    help="the migration directory containing index.yaml")
subparsers = parser.add_subparsers(dest="subCommand")
init_parser = subparsers.add_parser("init", help="Initialize the database with migration_info table(s)")
migrate_parser = subparsers.add_parser("migrate", help="Apply any outstanding migrations to the database.")
migrate_parser.add_argument("-f", "--from-version", dest="fromVersion", type=int, help="Revision to start migrating from")
migrate_parser.add_argument("-t", "--to-version", dest="toVersion", type=int, help="Revisiont to migrate to")
migrate_parser.add_argument("-s", "--select", dest="selectedMigrations", nargs="*", type=int, help="Run selected migrations by giving their index # from index.yaml")
list_parser = subparsers.add_parser("list", help="List all applied and outstanding migrations")


def getMigrator(migrationDirectory):
    indexFilepath = os.path.join(migrationDirectory, "index.yaml")
    migrator = DatabaseMigrator(indexFilepath)
    return migrator


def migrate(migrationDirectory, dsn,
            fromVersion=None, toVersion=None,
            selectedMigrations=None, init=False):
    migrator = getMigrator(migrationDirectory)
    migrator.connect(dsn)
    if init:
        models.init()
    migrator.migrate(fromVersion, toVersion, selectedMigrations)
    return migrator


def listMigrations(migrationDirectory, dsn, init=False):
    migrator = getMigrator(migrationDirectory)
    migrator.connect(dsn)
    if init:
        models.init()
    dbVersion = migrator.getVersion()
    print "Applied(*)  VersionNumber  MigrationName"
    for i, migration in enumerate(migrator.migrations):
        migrationVersion = i+1
        if migrationVersion <= dbVersion:
            print "%-10s  %-13s  %s"%("Y", migrationVersion, migration)
        else:
            print "%-10s  %-13s  %s"%("N ", migrationVersion, migration)


def initializeDatabase(dsn):
    models.connect(dsn)
    models.init()


def main(args, init=False):
    options = parser.parse_args(args)
    if options.subCommand == "migrate":
        print options.migrationDirectory
        print options.dsn
        print options.selectedMigrations
        migrate(options.migrationDirectory, options.dsn,
                fromVersion=options.fromVersion,
                toVersion=options.toVersion,
                selectedMigrations=options.selectedMigrations,
                init=init)
    elif options.subCommand == "list":
        listMigrations(options.migrationDirectory, options.dsn, init=init)
    elif options.subCommand == "init":
        initializeDatabase(options.dsn)
    return options
