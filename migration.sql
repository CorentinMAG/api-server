BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 26d193975219

DROP TABLE states;

DROP TABLE kafka_topic_parameters;

DROP TABLE periodical_parameters;

DROP TABLE transfer_policy_parameters;

DROP TABLE transfer_requests;

DROP TABLE transfer_policies;

DROP TABLE destination_policies;

DROP TABLE source_policies;

DROP TABLE credentials;

DROP TABLE targets;

DROP TABLE notification_servers;

DROP TABLE global_parameters;

DROP TABLE queues;

INSERT INTO alembic_version (version_num) VALUES ('26d193975219') RETURNING alembic_version.version_num;

-- Running upgrade 26d193975219 -> 996065456e04

CREATE TABLE queues (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    uid UUID NOT NULL, 
    priority INTEGER NOT NULL, 
    queue_timeout INTEGER NOT NULL, 
    queue_limit INTEGER NOT NULL, 
    CONSTRAINT queues_pkey PRIMARY KEY (id), 
    CONSTRAINT queues_name_key UNIQUE (name), 
    CONSTRAINT queues_uid_key UNIQUE (uid)
);

CREATE TABLE targets (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    protocol VARCHAR NOT NULL, 
    port INTEGER NOT NULL, 
    host VARCHAR NOT NULL, 
    CONSTRAINT targets_pkey PRIMARY KEY (id), 
    CONSTRAINT targets_name_key UNIQUE (name)
);

CREATE TABLE source_policies (
    id SERIAL NOT NULL, 
    purge BOOLEAN NOT NULL, 
    path VARCHAR, 
    bucket VARCHAR, 
    src_id INTEGER NOT NULL, 
    pattern VARCHAR, 
    CONSTRAINT source_policies_pkey PRIMARY KEY (id), 
    CONSTRAINT source_policies_src_id_fkey FOREIGN KEY(src_id) REFERENCES targets (id) ON DELETE CASCADE
);

CREATE TABLE destination_policies (
    id SERIAL NOT NULL, 
    path VARCHAR, 
    bucket VARCHAR, 
    dest_id INTEGER NOT NULL, 
    tmp_prefix_dest INTEGER NOT NULL, 
    final_prefix_dest INTEGER NOT NULL, 
    CONSTRAINT destination_policies_pkey PRIMARY KEY (id), 
    CONSTRAINT destination_policies_dest_id_fkey FOREIGN KEY(dest_id) REFERENCES targets (id) ON DELETE CASCADE
);

CREATE TYPE type AS ENUM ('PERIODICAL', 'COMMANDED');

CREATE TABLE transfer_policies (
    id SERIAL NOT NULL, 
    name VARCHAR(30) NOT NULL, 
    enabled BOOLEAN NOT NULL, 
    type type NOT NULL, 
    src_id INTEGER NOT NULL, 
    dest_id INTEGER NOT NULL, 
    queue_id INTEGER NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    CONSTRAINT transfer_policies_pkey PRIMARY KEY (id), 
    CONSTRAINT transfer_policies_dest_id_fkey FOREIGN KEY(dest_id) REFERENCES destination_policies (id) ON DELETE CASCADE, 
    CONSTRAINT transfer_policies_queue_id_fkey FOREIGN KEY(queue_id) REFERENCES queues (id), 
    CONSTRAINT transfer_policies_src_id_fkey FOREIGN KEY(src_id) REFERENCES source_policies (id) ON DELETE CASCADE, 
    CONSTRAINT transfer_policies_name_key UNIQUE (name)
);

CREATE TABLE transfer_requests (
    id SERIAL NOT NULL, 
    filename VARCHAR NOT NULL, 
    size INTEGER, 
    uid UUID NOT NULL, 
    policy_id INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    nb_retry INTEGER, 
    next_retry_min_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    CONSTRAINT transfer_requests_pkey PRIMARY KEY (id), 
    CONSTRAINT transfer_requests_policy_id_fkey FOREIGN KEY(policy_id) REFERENCES transfer_policies (id) ON DELETE SET NULL, 
    CONSTRAINT transfer_requests_uid_key UNIQUE (uid)
);

CREATE TYPE state AS ENUM ('QUEUED', 'SUCCESSFUL', 'FAILED', 'CANCELLED', 'NOTIFY', 'IN_PROGRESS');

CREATE TYPE sub_state AS ENUM ('CHECK', 'VALIDATION', 'DESTINATION_COPY', 'NOTIFY', 'STOPPED', 'SOURCE_COPY');

CREATE TABLE states (
    id SERIAL NOT NULL, 
    state state NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    request_id INTEGER NOT NULL, 
    failure_reason VARCHAR, 
    sub_state sub_state, 
    CONSTRAINT states_pkey PRIMARY KEY (id), 
    CONSTRAINT states_request_id_fkey FOREIGN KEY(request_id) REFERENCES transfer_requests (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE notification_servers (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    type VARCHAR NOT NULL, 
    host VARCHAR NOT NULL, 
    port INTEGER NOT NULL, 
    timeout INTEGER NOT NULL, 
    CONSTRAINT notification_servers_pkey PRIMARY KEY (id), 
    CONSTRAINT notification_servers_name_key UNIQUE (name)
);

CREATE TABLE credentials (
    id SERIAL NOT NULL, 
    login VARCHAR NOT NULL, 
    password VARCHAR NOT NULL, 
    token VARCHAR, 
    type VARCHAR NOT NULL, 
    target_id INTEGER, 
    server_id INTEGER, 
    CONSTRAINT credentials_pkey PRIMARY KEY (id), 
    CONSTRAINT credentials_server_id_fkey FOREIGN KEY(server_id) REFERENCES notification_servers (id) ON DELETE CASCADE, 
    CONSTRAINT credentials_target_id_fkey FOREIGN KEY(target_id) REFERENCES targets (id) ON DELETE CASCADE
);

CREATE TYPE mode AS ENUM ('ONLINE', 'OFFLINE');

CREATE TABLE global_parameters (
    id SERIAL NOT NULL, 
    mode mode NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    tmp_prefix_dest INTEGER NOT NULL, 
    final_prefix_dest INTEGER NOT NULL, 
    max_retry INTEGER NOT NULL, 
    retry_delay INTEGER NOT NULL, 
    transfer_requests_history INTEGER NOT NULL, 
    compress BOOLEAN NOT NULL, 
    only_new_data BOOLEAN NOT NULL, 
    transfer_timeout INTEGER NOT NULL, 
    queue_timeout INTEGER NOT NULL, 
    polling_interval INTEGER NOT NULL, 
    CONSTRAINT global_parameters_pkey PRIMARY KEY (id)
);

CREATE TABLE kafka_parameters (
    id SERIAL NOT NULL, 
    topic VARCHAR NOT NULL, 
    replica INTEGER NOT NULL, 
    partitions INTEGER NOT NULL, 
    server_id INTEGER NOT NULL, 
    policy_id INTEGER NOT NULL, 
    CONSTRAINT kafka_parameters_pkey PRIMARY KEY (id), 
    CONSTRAINT kafka_parameters_policy_id_fkey FOREIGN KEY(policy_id) REFERENCES transfer_policies (id) ON DELETE CASCADE, 
    CONSTRAINT kafka_parameters_server_id_fkey FOREIGN KEY(server_id) REFERENCES notification_servers (id) ON DELETE CASCADE
);

CREATE TABLE periodical_parameters (
    id SERIAL NOT NULL, 
    polling_interval INTEGER NOT NULL, 
    parameter_id INTEGER NOT NULL, 
    next_polling_min_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    CONSTRAINT periodical_parameters_pkey PRIMARY KEY (id), 
    CONSTRAINT periodical_parameters_parameter_id_fkey FOREIGN KEY(parameter_id) REFERENCES transfer_parameters (id) ON DELETE CASCADE
);

CREATE TABLE notification_servers (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    type VARCHAR NOT NULL, 
    host VARCHAR NOT NULL, 
    port INTEGER NOT NULL, 
    timeout INTEGER NOT NULL, 
    CONSTRAINT notification_servers_pkey PRIMARY KEY (id), 
    CONSTRAINT notification_servers_name_key UNIQUE (name)
);

CREATE TABLE transfer_parameters (
    id SERIAL NOT NULL, 
    max_retry INTEGER NOT NULL, 
    retry_delay INTEGER NOT NULL, 
    transfer_requests_history INTEGER NOT NULL, 
    pattern VARCHAR NOT NULL, 
    compress BOOLEAN NOT NULL, 
    compress_type VARCHAR, 
    data_type VARCHAR NOT NULL, 
    policy_id INTEGER NOT NULL, 
    only_new_data BOOLEAN NOT NULL, 
    transfer_timeout INTEGER NOT NULL, 
    queue_timeout INTEGER NOT NULL, 
    polling_interval INTEGER NOT NULL, 
    CONSTRAINT transfer_parameters_pkey PRIMARY KEY (id), 
    CONSTRAINT transfer_parameters_policy_id_fkey FOREIGN KEY(policy_id) REFERENCES transfer_policies (id) ON DELETE CASCADE
);

CREATE TABLE destination_policies (
    id SERIAL NOT NULL, 
    path VARCHAR, 
    bucket VARCHAR, 
    dest_id INTEGER NOT NULL, 
    CONSTRAINT destination_policies_pkey PRIMARY KEY (id), 
    CONSTRAINT destination_policies_dest_id_fkey FOREIGN KEY(dest_id) REFERENCES targets (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='996065456e04' WHERE alembic_version.version_num = '26d193975219';

COMMIT;

