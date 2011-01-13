import os
import unittest

import oursql

from goose import goose
from goose import testsettings as config


class TestMigration(unittest.TestCase):
    def setUp(self):
        self.indexFilepath = os.path.join(goose.ROOT, "testmigrations",
                                          "index.yaml")
        self.migrator = goose.DatabaseMigrator(self.indexFilepath)
        self.connection = oursql.connect(user=config.USERNAME,
                                         passwd=config.PASSWORD,
                                         host=config.HOST, port=config.PORT)

    def tearDown(self):
        cursor = self.connection.cursor()
        cursor.execute("DROP DATABASE IF EXISTS %s;"%(config.DB,))

    def test_connectCreateDbIfNecessary(self):
        self.migrator.connect(user=config.USERNAME,
                              password=config.PASSWORD,
                              host=config.HOST,
                              port=config.PORT,
                              db=config.DB)

    def test_getVersionWithoutVersionInfo(self):
        self.migrator.connect(user=config.USERNAME,
                              password=config.PASSWORD,
                              host=config.HOST,
                              port=config.PORT,
                              db=config.DB)
        self.assertEquals(self.migrator.getVersion(), None)

    def test_installMigrationInfoVersionNumberWithNoMigrations(self):
        self.migrator.connect(user=config.USERNAME,
                              password=config.PASSWORD,
                              host=config.HOST,
                              port=config.PORT,
                              db=config.DB)
        self.migrator.installMigrationInfo()
        self.assertEquals(self.migrator.getVersion(), None)

    def test_createAndMigrate(self):
        self.migrator.connect(user=config.USERNAME,
                              password=config.PASSWORD,
                              host=config.HOST,
                              port=config.PORT,
                              db=config.DB)
        self.migrator.installMigrationInfo()
        migrationsApplied = self.migrator.migrate()
        self.assertEqual(migrationsApplied, ["create.sql",
                                             "track.sql"])
        self.assertEqual(self.migrator.getVersion(), 2)
        cursor = self.connection.cursor()
        cursor.execute("USE %s;"%(config.DB,))
        cursor.execute("SELECT * FROM test1;")
        cursor.execute("SELECT * FROM Track;")
        migrationsApplied = self.migrator.migrate()
        self.assertEqual(migrationsApplied, [])
        self.assertEqual(self.migrator.getVersion(), 2)

