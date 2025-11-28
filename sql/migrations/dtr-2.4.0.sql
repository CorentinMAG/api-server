BEGIN;

-- Running upgrade 1d33f8699e8d -> dcd8e4cda5f9

CREATE TABLE triggers (
    name VARCHAR NOT NULL, 
    polling_interval INTEGER NOT NULL, 
    id SERIAL NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

COMMENT ON COLUMN triggers.polling_interval IS 'seconds';

CREATE INDEX ix_triggers_created_at ON triggers (created_at);

CREATE UNIQUE INDEX ix_triggers_name ON triggers (name);

CREATE TABLE workers (
    name VARCHAR NOT NULL, 
    id SERIAL NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_workers_created_at ON workers (created_at);

CREATE UNIQUE INDEX ix_workers_name ON workers (name);

CREATE TABLE worker_queues (
    worker_id INTEGER, 
    queue_id INTEGER, 
    FOREIGN KEY(queue_id) REFERENCES queues (id), 
    FOREIGN KEY(worker_id) REFERENCES workers (id)
);

DROP TABLE periodical_parameters;

ALTER TABLE credentials ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE credentials ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_credentials_created_at ON credentials (created_at);

ALTER TABLE destination_policies ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE destination_policies ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE destination_policies ALTER COLUMN dest_id DROP NOT NULL;

CREATE INDEX ix_destination_policies_created_at ON destination_policies (created_at);

ALTER TABLE global_parameters ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE global_parameters ALTER COLUMN updated_at DROP NOT NULL;

CREATE INDEX ix_global_parameters_created_at ON global_parameters (created_at);

ALTER TABLE notification_servers ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE notification_servers ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_notification_servers_created_at ON notification_servers (created_at);

ALTER TABLE queues ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE queues ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_queues_created_at ON queues (created_at);

ALTER TABLE server_parameters ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE server_parameters ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_server_parameters_created_at ON server_parameters (created_at);

ALTER TABLE source_policies ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE source_policies ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE source_policies ALTER COLUMN src_id DROP NOT NULL;

CREATE INDEX ix_source_policies_created_at ON source_policies (created_at);

ALTER TABLE states ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_states_created_at ON states (created_at);

ALTER TABLE target_parameters ADD COLUMN http_proxy VARCHAR;

ALTER TABLE target_parameters ADD COLUMN https_proxy VARCHAR;

ALTER TABLE target_parameters ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE target_parameters ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_target_parameters_created_at ON target_parameters (created_at);

ALTER TABLE target_parameters DROP CONSTRAINT target_parameters_target_id_fkey;

ALTER TABLE target_parameters ADD FOREIGN KEY(target_id) REFERENCES targets (id) ON DELETE CASCADE;

ALTER TABLE targets ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE targets ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_targets_created_at ON targets (created_at);

ALTER TABLE transfer_policies ADD COLUMN trigger_id INTEGER;

ALTER TABLE transfer_policies ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE transfer_policies ALTER COLUMN src_id DROP NOT NULL;

ALTER TABLE transfer_policies ALTER COLUMN queue_id DROP NOT NULL;

CREATE INDEX ix_transfer_policies_created_at ON transfer_policies (created_at);

ALTER TABLE transfer_policies DROP CONSTRAINT transfer_policies_queue_id_fkey;

ALTER TABLE transfer_policies ADD FOREIGN KEY(queue_id) REFERENCES queues (id) ON DELETE CASCADE;

ALTER TABLE transfer_policies ADD FOREIGN KEY(trigger_id) REFERENCES triggers (id);

ALTER TABLE transfer_policy_parameters ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL;

ALTER TABLE transfer_policy_parameters ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX ix_transfer_policy_parameters_created_at ON transfer_policy_parameters (created_at);

ALTER TABLE transfer_requests ADD COLUMN multi_dest_uid UUID;

ALTER TABLE transfer_requests ADD COLUMN current_state_id INTEGER;

ALTER TABLE transfer_requests ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE transfer_requests ALTER COLUMN size TYPE BIGINT;

ALTER TABLE transfer_requests DROP CONSTRAINT transfer_requests_uid_key;

CREATE INDEX ix_transfer_requests_filename ON transfer_requests (filename);

CREATE INDEX ix_transfer_requests_multi_dest_uid ON transfer_requests (multi_dest_uid);

CREATE UNIQUE INDEX ix_transfer_requests_uid ON transfer_requests (uid);

ALTER TABLE transfer_requests ADD FOREIGN KEY(current_state_id) REFERENCES states (id) ON DELETE SET NULL;

UPDATE alembic_version SET version_num='dcd8e4cda5f9' WHERE alembic_version.version_num = '1d33f8699e8d';

COMMIT;

