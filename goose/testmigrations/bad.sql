insert into track (trackId) values (7);

-- The following syntax error should cause this transaction to fail
-- This file is just a test that a failing transaction does the
-- right thing.  Basically, this migration should not be aplied
-- but any other migrations before this should be applied.

-- Of course, SQLite isn't able to rollback DDL so migrations
-- containing create table statements that later have syntax errors
-- will not be rolledback.

SELECT * FRO Track;