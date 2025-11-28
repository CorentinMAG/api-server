BEGIN;

-- Running upgrade dcd8e4cda5f9 -> a6802cc0e9c3

UPDATE alembic_version SET version_num='a6802cc0e9c3' WHERE alembic_version.version_num = 'dcd8e4cda5f9';

COMMIT;

