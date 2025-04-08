-- TABLE
DROP TABLE IF EXISTS _qk_cache;
CREATE UNLOGGED TABLE _qk_cache (
    id serial PRIMARY KEY,
    key text UNIQUE NOT NULL,
    value bytea,
    inserted_at timestamp,
    expire_at timestamp
);

-- INDEX
DROP INDEX IF EXISTS idx_cache_key;
CREATE INDEX idx_cache_key ON _qk_cache (key);
DROP INDEX IF EXISTS idx_cache_expire_at;
CREATE INDEX idx_cache_expire_at ON _qk_cache (expire_at);

-- PROCEDURE
CREATE OR REPLACE PROCEDURE _qk_expire_rows () AS
$$
BEGIN
    DELETE FROM _qk_cache
    WHERE expire_at <= NOW();

    COMMIT;
END;
$$ LANGUAGE plpgsql;

CALL _qk_expire_rows();

-- (cron db) Create a schedule to run the procedure every hour
SELECT cron.schedule_in_database('_qk_expire_rows', '0 * * * *', $$CALL _qk_expire_rows();$$, 'chem_synth_core');

-- List all scheduled jobs
SELECT * FROM cron.job;