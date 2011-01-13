# __init__.py

import os
import unittest

from goose import goose


class FakeCursor(object):
    def __init__(self, result=[]):
        self.result = result

    def execute(self, *args, **kwargs):
        pass

    def fetchall(self):
        return self.result

    def close(self):
        pass


class RecordingCursor(object):
    def __init__(self):
        self.statements = []

    def execute(self, query):
        self.statements.append(query)


class TestDatabaseMigrator(unittest.TestCase):
    """Tests that don't require database setup"""
    def setUp(self):
        self.indexFilepath = os.path.join(goose.ROOT, "testmigrations", "index.yaml")
        self.migrator = goose.DatabaseMigrator(self.indexFilepath)

    def test_missingMigration(self):
        index = {"migrations":["create.sql", "fake.sql"]}
        self.assertRaises(ValueError, goose.DatabaseMigrator,
                          self.indexFilepath, index=index)

    def test_schemaFiles(self):
        self.assertEqual(self.migrator.migrations, ["create.sql",
                                                    "track.sql",
                                                    ])

    def test_firstMigration(self):
        self.assertEqual(self.migrator.migrations[0], "create.sql")
            
    def test_secondMigration(self):
        self.assertEqual(self.migrator.migrations[1], "track.sql")

    def test_migrateToVersion0to1(self):
        """Should return the 0th migration:
        """
        migrations = self.migrator.howToMigrate(0, 1)
        self.assertEqual(migrations, ["create.sql",
                                      ])

    def test_migrateToVersion0to2(self):
        """Should return the two migrations necessary to reach version 1
        """
        migrations = self.migrator.howToMigrate(0, 2)
        self.assertEqual(migrations, ["create.sql",
                                      "track.sql"])
        
    def test_migrateToVersion1to2(self):
        """Should return the two migrations necessary to reach version 1
        """
        migrations = self.migrator.howToMigrate(1, 2)
        self.assertEqual(migrations, ["track.sql"])

    def test_migrateToVersion2(self):
        """Should return the two migrations necessary to reach version 1
        """
        migrations = self.migrator.howToMigrate(2)
        self.assertEqual(migrations, [])

    def test_migrateFromEmptyMigrations(self):
        migrations = self.migrator.howToMigrate(None)
        self.assertEqual(migrations, ["create.sql",
                                      "track.sql"])

    def test_getVersion(self):
        self.migrator.db = "test"
        cursor = FakeCursor([(1,)])
        self.assertEqual(self.migrator.getVersion(cursor), 1)


class TestExecuteBatch(unittest.TestCase):
    def test_singleStatement(self):
        cursor = RecordingCursor()
        sql = """SELECT 1;"""
        goose.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, ["SELECT 1",])

    def test_twoStatements(self):
        cursor = RecordingCursor()
        sql = """SELECT 1;
SELECT 2;
"""
        goose.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, ["SELECT 1",
                                              "\nSELECT 2"])

    def test_justComments(self):
        cursor = RecordingCursor()
        sql = """-- hello world
"""
        goose.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, [])

    def test_commentsAndStatements(self):
        cursor = RecordingCursor()
        sql = """-- hello world
SELECT 1;
SELECT 2;
-- another comment
select 3
"""
        goose.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, ["SELECT 1",
                                              "\nSELECT 2",
                                              "\nselect 3"])
        
        
        
