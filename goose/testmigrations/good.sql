-- This migration is just here to confirm that we don't continue
-- applying migrations after one fails.

CREATE  TABLE TransactionStoppedUs (
        id INT);

        