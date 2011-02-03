import os
import unittest

import sqlite3

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
        
