# __init__.py

import json
import os
import unittest

from goose import core


class FakeResult(object):
    def __init__(self, result):
        self.result = result

    def scalar(self):
        return self.result[0][0]


class FakeSession(object):
    def __init__(self, result=[]):
        self.result = result

    def query(self, arg):
        return FakeResult(self.result)


class TestDatabaseMigrator(unittest.TestCase):
    """Tests that don't require database setup"""
    def setUp(self):
        self.indexFilepath = os.path.join(core.ROOT, "testmigrations", "index.yaml")
        self.migrator = core.DatabaseMigrator(self.indexFilepath)

    def test_missingMigration(self):
        index = {"migrations":["create.sql", "fake.sql"]}
        self.assertRaises(ValueError, core.DatabaseMigrator,
                          self.indexFilepath, index=index)

    def test_schemaFiles(self):
        self.assertEqual(self.migrator.migrations, ["create.sql",
                                                    "track.sql",
                                                    "bad.sql",
                                                    "good.sql",
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

    def test_migrateFromVersion2(self):
        """Should return the two migrations after version 2
        """
        migrations = self.migrator.howToMigrate(2)
        self.assertEqual(migrations, ["bad.sql", "good.sql"])

    def test_migrateFromVersion4(self):
        """Should return no migrations
        """
        migrations = self.migrator.howToMigrate(4)
        self.assertEqual(migrations, [])

    def test_migrateFromEmptyMigrations(self):
        migrations = self.migrator.howToMigrate(None)
        self.assertEqual(migrations, ["create.sql",
                                      "track.sql",
                                      "bad.sql",
                                      "good.sql",])

    def test_getVersion(self):
        self.migrator.db = "test"
        session = FakeSession([(1,)])
        self.assertEqual(self.migrator.getVersion(session), 1)


class RecordingCursor(object):
    def __init__(self):
        self.statements = []

    def execute(self, query):
        self.statements.append(query)


class TestJsonConfig(unittest.TestCase):
    def setUp(self):
        self.config = os.path.join(core.ROOT, "testmigrations",
                                   "index.json")

    def test_is_valid_json(self):
        data = None
        try:
            with open(self.config, "r") as f:
                data = json.load(f)
        except Exception:
            pass
        self.assertTrue(data is not None, "Data should be a dictionary")




class TestDatabaseMigratorJSON(TestDatabaseMigrator):
    """
    First lets confirm that a json file with the same contents passes
    the same set of tests.

    This will verify that both the PyYAML parser will parse
    json documents and then I can test and implement the fallback.
    """
    def setUp(self):
        self.indexFilepath = os.path.join(core.ROOT, "testmigrations", "index.json")
        self.migrator = core.DatabaseMigrator(self.indexFilepath)


class TestExecuteBatch(unittest.TestCase):
    def test_singleStatement(self):
        cursor = RecordingCursor()
        sql = """SELECT 1;"""
        core.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, ["SELECT 1",])

    def test_mysqlStoredProcDelimiter(self):
        """Goose should handle stored procedures using the DELIMITER statements

        MySQL uses DELIMITER ;;

        The actual delimiter doesn't actually matter for our use case
        as any stored proc will be bracketed in its own set of DELIMITER statements.

        And currently executeBatch parses that as "DELIMITER "
        by consuming all the semicolons.

        """
        cursor = RecordingCursor()
        sql = """DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_insertLog`(
      _hash char(32),
      _event char(10),
      _id int(10),
      _ip char(15)
      )
begin
   declare sameRow int(1);
    select count(*) into sameRow from log
      where  event = _event and ip = _ip and id = _id and `hash` = _hash
      and TIMESTAMPDIFF(HOUR, dateAdded, now()) < 1;
    if (sameRow <= 0)  then
       insert into log (`hash`, event, id, ip) values (_hash, _event, _id, _ip);
    end if;
end;;
DELIMITER ;
        """
        core.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements,
                          ['\nCREATE DEFINER=`root`@`localhost` PROCEDURE `sp_insertLog`(\n      _hash char(32),\n      _event char(10),\n      _id int(10),\n      _ip char(15)\n      )\nbegin\n   declare sameRow int(1);\n    select count(*) into sameRow from log\n      where  event = _event and ip = _ip and id = _id and `hash` = _hash\n      and TIMESTAMPDIFF(HOUR, dateAdded, now()) < 1;\n    if (sameRow <= 0)  then\n       insert into log (`hash`, event, id, ip) values (_hash, _event, _id, _ip);\n    end if;\nend'])

    def test_postgresqlStoredProc(self):
        """And of course PGSQL syntax just works...  I miss you PostgreSQL.

        """
        cursor = RecordingCursor()
        sql = """
CREATE FUNCTION add_three_values(v1 anyelement, v2 anyelement, v3 anyelement)
RETURNS anyelement AS $$
DECLARE
    result ALIAS FOR $0;
BEGIN
    result := v1 + v2 + v3;
    RETURN result;
END;
$$ LANGUAGE plpgsql;
        """
        core.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, ['CREATE FUNCTION add_three_values(v1 anyelement, v2 anyelement, v3 anyelement)\nRETURNS anyelement AS $$\nDECLARE\n    result ALIAS FOR $0',
 '\nBEGIN\n    result := v1 + v2 + v3',
 '\n    RETURN result',
 '\nEND',
 '\n$$ LANGUAGE plpgsql'])


    def test_twoStatements(self):
        cursor = RecordingCursor()
        sql = """SELECT 1;
SELECT 2;
"""
        core.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, ["SELECT 1",
                                              "\nSELECT 2"])

    def test_justComments(self):
        cursor = RecordingCursor()
        sql = """-- hello world
"""
        core.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, [])

    def test_commentsAndStatements(self):
        cursor = RecordingCursor()
        sql = """-- hello world
SELECT 1;
SELECT 2;
-- another comment
select 3
"""
        core.executeBatch(cursor, sql)
        self.assertEquals(cursor.statements, ["SELECT 1",
                                              "\nSELECT 2",
                                              "\nselect 3"])



