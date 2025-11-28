BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 1d33f8699e8d

CREATE TYPE mode AS ENUM ('ONLINE', 'OFFLINE');

CREATE TABLE global_parameters (
    id SERIAL NOT NULL, 
    mode mode NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    tmp_prefix VARCHAR, 
    final_prefix VARCHAR, 
    retry_delay INTEGER, 
    max_retry INTEGER, 
    transfer_requests_history INTEGER NOT NULL, 
    only_new_data BOOLEAN NOT NULL, 
    transfer_timeout INTEGER NOT NULL, 
    queue_timeout INTEGER NOT NULL, 
    polling_interval INTEGER NOT NULL, 
    queue_limit INTEGER NOT NULL, 
    queue_threshold INTEGER NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE notification_servers (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    type VARCHAR NOT NULL, 
    host VARCHAR NOT NULL, 
    port INTEGER NOT NULL, 
    timeout INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (name)
);

CREATE TABLE queues (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    uid UUID NOT NULL, 
    priority INTEGER NOT NULL, 
    queue_timeout INTEGER, 
    queue_limit INTEGER, 
    queue_threshold INTEGER, 
    PRIMARY KEY (id), 
    UNIQUE (name), 
    UNIQUE (uid)
);

CREATE INDEX ix_queues_priority ON queues (priority);

CREATE TYPE protocol AS ENUM ('FTPS', 'SFTP', 'S3', 'HTTP');

CREATE TABLE targets (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    protocol protocol NOT NULL, 
    port INTEGER NOT NULL, 
    host VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (name)
);

CREATE TABLE credentials (
    id SERIAL NOT NULL, 
    login VARCHAR NOT NULL, 
    password VARCHAR NOT NULL, 
    target_id INTEGER, 
    server_id INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(server_id) REFERENCES notification_servers (id) ON DELETE CASCADE, 
    FOREIGN KEY(target_id) REFERENCES targets (id) ON DELETE CASCADE
);

CREATE TABLE source_policies (
    id SERIAL NOT NULL, 
    purge BOOLEAN NOT NULL, 
    path VARCHAR, 
    bucket VARCHAR, 
    pattern VARCHAR NOT NULL, 
    src_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(src_id) REFERENCES targets (id) ON DELETE CASCADE
);

CREATE TABLE target_parameters (
    id SERIAL NOT NULL, 
    use_ssl BOOLEAN NOT NULL, 
    verify BOOLEAN NOT NULL, 
    target_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(target_id) REFERENCES targets (id)
);

CREATE TYPE type AS ENUM ('PERIODICAL', 'COMMANDED');

CREATE TABLE transfer_policies (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    enabled BOOLEAN NOT NULL, 
    type type NOT NULL, 
    src_id INTEGER NOT NULL, 
    queue_id INTEGER NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(queue_id) REFERENCES queues (id), 
    FOREIGN KEY(src_id) REFERENCES source_policies (id) ON DELETE CASCADE, 
    UNIQUE (name)
);

CREATE TABLE destination_policies (
    id SERIAL NOT NULL, 
    path VARCHAR, 
    bucket VARCHAR, 
    dest_id INTEGER NOT NULL, 
    policy_id INTEGER NOT NULL, 
    tmp_prefix VARCHAR, 
    final_prefix VARCHAR, 
    path_from_filename_delimiter VARCHAR, 
    path_from_filename_expression JSON, 
    PRIMARY KEY (id), 
    FOREIGN KEY(dest_id) REFERENCES targets (id) ON DELETE CASCADE, 
    FOREIGN KEY(policy_id) REFERENCES transfer_policies (id) ON DELETE CASCADE
);

CREATE TABLE transfer_policy_parameters (
    id SERIAL NOT NULL, 
    max_retry INTEGER, 
    retry_delay INTEGER, 
    transfer_requests_history INTEGER, 
    only_new_data BOOLEAN, 
    transfer_timeout INTEGER, 
    policy_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(policy_id) REFERENCES transfer_policies (id) ON DELETE CASCADE
);

CREATE TABLE periodical_parameters (
    id SERIAL NOT NULL, 
    polling_interval INTEGER NOT NULL, 
    parameter_id INTEGER NOT NULL, 
    next_polling_min_time TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(parameter_id) REFERENCES transfer_policy_parameters (id) ON DELETE CASCADE
);

CREATE TABLE server_parameters (
    id SERIAL NOT NULL, 
    type VARCHAR NOT NULL, 
    dest_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(dest_id) REFERENCES destination_policies (id) ON DELETE CASCADE
);

CREATE TABLE transfer_requests (
    id SERIAL NOT NULL, 
    filename VARCHAR NOT NULL, 
    size FLOAT, 
    uid UUID NOT NULL, 
    follows_from_task UUID, 
    policy_id INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    nb_retry INTEGER NOT NULL, 
    next_retry_min_time TIMESTAMP WITHOUT TIME ZONE, 
    start TIMESTAMP WITHOUT TIME ZONE, 
    "end" TIMESTAMP WITHOUT TIME ZONE, 
    download_rate FLOAT, 
    download_time FLOAT, 
    upload_rate FLOAT, 
    upload_time FLOAT, 
    dest_id INTEGER, 
    src_relative_path VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(dest_id) REFERENCES destination_policies (id) ON DELETE SET NULL, 
    FOREIGN KEY(policy_id) REFERENCES transfer_policies (id) ON DELETE SET NULL, 
    UNIQUE (uid)
);

CREATE INDEX ix_transfer_requests_created_at ON transfer_requests (created_at);

CREATE INDEX ix_transfer_requests_next_retry_min_time ON transfer_requests (next_retry_min_time);

CREATE INDEX ix_transfer_requests_size ON transfer_requests (size);

CREATE TABLE kafka_topic_parameters (
    id INTEGER NOT NULL, 
    topic VARCHAR NOT NULL, 
    replica INTEGER, 
    partitions INTEGER, 
    server_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES server_parameters (id) ON DELETE CASCADE, 
    FOREIGN KEY(server_id) REFERENCES notification_servers (id) ON DELETE CASCADE
);

CREATE TYPE state AS ENUM ('QUEUED', 'SUCCESSFUL', 'FAILED', 'CANCELLED', 'IN_PROGRESS');

CREATE TYPE substate AS ENUM ('NOTIFY', 'NOTIFIED');

CREATE TABLE states (
    id SERIAL NOT NULL, 
    state state NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    request_id INTEGER NOT NULL, 
    failure_reason VARCHAR, 
    sub_state substate, 
    PRIMARY KEY (id), 
    FOREIGN KEY(request_id) REFERENCES transfer_requests (id) ON DELETE CASCADE
);

CREATE INDEX ix_states_request_id ON states (request_id);

CREATE INDEX ix_states_state ON states (state);

CREATE INDEX ix_states_sub_state ON states (sub_state);

INSERT INTO alembic_version (version_num) VALUES ('1d33f8699e8d') RETURNING alembic_version.version_num;

COMMIT;

