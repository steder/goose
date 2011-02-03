import os
import unittest

from goose import core
from goose import models

dbFile = ":memory:"
dbUrl = "sqlite:///%s"%(dbFile,)


class TestMigration(unittest.TestCase):
    def setUp(self):
        self.indexFilepath = os.path.join(core.ROOT, "testmigrations",
                                          "index.yaml")
        self.migrator = core.DatabaseMigrator(self.indexFilepath)
        self.migrator.connect(dbUrl)
        models.init()

    def tearDown(self):
        pass

    def test_connectCreateDbIfNecessary(self):
        self.migrator.connect(dbUrl)
        
    def test_getVersionWithoutVersionInfo(self):
        self.migrator.connect(dbUrl)
        self.assertRaises(ValueError, self.migrator.getVersion)

    def test_installMigrationInfoVersionNumberWithNoMigrations(self):
        self.assertEquals(self.migrator.getVersion(), None)

    def test_createAndMigrate(self):
        # we migrate only to version 2 because the test migrations
        # after that are supposed to fail.
        migrationsApplied = self.migrator.migrate(toVersion=2)
        self.assertEqual(migrationsApplied, ["create.sql",
                                             "track.sql"])
        self.assertEqual(self.migrator.getVersion(), 2)
        cursor = self.migrator.session
        cursor.execute("SELECT * FROM test1;")
        cursor.execute("SELECT * FROM Track;")
        migrationsApplied = self.migrator.migrate(toVersion=2)
        self.assertEqual(migrationsApplied, [])
        self.assertEqual(self.migrator.getVersion(), 2)
        
    def test_migrationFailure(self):
        # here we attempt to migration all the way but our 3rd test
        # migration contains and error so we'll only get to the first 2.
        self.assertRaises(models.OperationalError, self.migrator.migrate)
        self.assertEqual(self.migrator.getVersion(), 2)
        migrations = self.migrator.migrationsApplied()
        for migration in migrations:
            print migration

        migrationsApplied = self.migrator.migrate(toVersion=2)
        self.assertEqual(migrationsApplied, [])
        self.assertEqual(self.migrator.getVersion(), 2)
        

class TestMigrateSubcommandFunction(unittest.TestCase):
    def setUp(self):
        migrationDir = os.path.join(core.ROOT, "testmigrations")
        self.migrator = core.migrate(migrationDir, dbUrl, toVersion=2, init=True)

    def test_migrations(self):
        self.assertEquals(self.migrator.migrations,
                          ["create.sql",
                           "track.sql",
                           "bad.sql",
                           "good.sql"])


class TestListSubcommandFunction(unittest.TestCase):
    def test_listMigrations(self):
        migrationDir = os.path.join(core.ROOT, "testmigrations")
        core.listMigrations(migrationDir, dbUrl, init=True)


class TestInitializeSubcommandFunction(unittest.TestCase):
    def test(self):
        models.connect(dbUrl)
        models.init()
    

class TestMain(unittest.TestCase):
    def setUp(self):
        self.migrationDir = os.path.join(core.ROOT, "testmigrations")

    def test_init(self):
        args = ["-m", self.migrationDir, "-d", dbUrl, "init"]
        options = core.main(args)
        self.assertEquals(options.subCommand, "init")

    def test_list(self):
        args = ["-m", self.migrationDir, "-d", dbUrl, "list"]
        options = core.main(args, init=True)
        self.assertEquals(options.subCommand, "list")

    def test_migrate(self):
        args = ["-m", self.migrationDir, "-d", dbUrl, "migrate",
                "-t", "2"]
        options = core.main(args, init=True)
        self.assertEquals(options.subCommand, "migrate")
