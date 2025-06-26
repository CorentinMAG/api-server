# 🧠 **API Server** 🧠

---

## 📝 **Overview**

The ***API Server*** is the **central brain** of the DTR microservices architecture. It *orchestrates* all data transfer operations by managing *policies*, *requests*, and *notifications*. This service provides a *RESTful API* that enables communication between all DTR components, maintains the *database state*, and ensures *system consistency*.

---

## 📌 **Architecture and Operation**

### 🔄 **Workflow Diagram**

```
+----------------------+       API Requests         +-----------------------+
|                      |--------------------------->|                       |
|    DTR Services      |                            |      API Server       |
|                      |<---------------------------|                       |
+----------+-----------+      API Responses         +-----------------------+
           |                                          |
           |                                          | Database Operations
           |                                          v
+----------------------+       Data Access          +-----------------------+
|                      |--------------------------->|                       |
|   Database Layer     |                            |    PostgreSQL DB      |
|                      |<---------------------------|                       |
+----------------------+      Query Results         +-----------------------+
```

---

## 📖 **Detailed Operation**

1. ***Initialization***: The API server initializes with predefined *environment variables*, *database connections*, and *API endpoints*.

2. ***API Endpoints***:

   - **Policy Management**:
     - Create/update/delete transfer policies
     - List active policies
     - Validate policy configurations

   - **Request Handling**:
     - Create transfer requests
     - Update request states
     - Monitor request progress
     - Handle request timeouts

   - **Notification Management**:
     - Queue notifications
     - Track notification status
     - Handle notification retries

   - **System Status**:
     - Health checks
     - Performance metrics
     - System configuration

3. ***Database Operations***:

   - **Schema Management**:
     - Automatic migrations via Alembic
     - Version control of database schema
     - Rollback capabilities

   - **Data Consistency**:
     - Transaction management
     - Data validation
     - State tracking

4. ***Security Features***:

   - Authentication mechanisms
   - Authorization controls
   - Data encryption
   - Audit logging

---

## 🛠️ **Environment Variables**

Environment variables are managed via GitLab CI and Docker Compose:

| Variable Name            | Description                                 | Default Value                  |
| ------------------------ | ------------------------------------------- | ------------------------------ |
| `DTR_DB_NAME`           | Database name                               | `dtr`                          |
| `DTR_DB_USER`           | Database user                               | `postgres`                     |
| `DTR_DB_PASSWORD`       | Database password                           | ***Required***                 |
| `DTR_DB_HOST`           | Database host                               | `127.0.0.1`                    |
| `DTR_DB_PORT`           | Database port                               | `5432`                         |
| `DTR_DB_CREATE`         | Create database schema                      | `false`                        |
| `DTR_API_VERSION`       | API version                                 | Managed by CI (`$DOCKER_TAG`)  |
| `DTR_LOG_LEVEL`         | Log verbosity level                         | `INFO`                         |
| `DTR_ENCRYPTION_KEY`    | Encryption key for sensitive data           | ***Required***                 |

---

## 💻 **Development Environment**

In *development*, Docker Compose manages the environment (refer to main `compose.yml`). **API server specifics**:

```yaml
api:
  image: $AFORGE_HOST/dtr-docker/api-server:$API_VERSION
  container_name: api
  build:
    context: .
    dockerfile: api-server/Dockerfile.dev
    args:
    - AFORGE_HOST
    - AFORGE_USER
    - AFORGE_PASSWORD
    - AFORGE_PIP_REPO
    - AFORGE_PIP_DTR
    - AFORGE_ALPINE_REPO
    - DOCKER_TAG=$API_VERSION
  ports:
  - 9000:80
  environment:
  - DTR_DB_NAME
  - DTR_DB_USER
  - DTR_DB_PASSWORD
  - DTR_DB_PORT
  - DTR_LOG_LEVEL=DEBUG
  - DTR_DB_CREATE=true
  - PYTHONUNBUFFERED
  - DTR_DB_HOST
  - DTR_ENCRYPTION_KEY
  volumes:
  - ./api-server/api:/opt/app/api
```

---

## 🔧 **Database Migrations**

The API server uses Alembic for database migrations:

1. **Create Migration**:
```bash
   alembic revision --autogenerate -m "description"
   ```

2. **Apply Migration**:
```bash
   alembic upgrade head
```

3. **Generate SQL Script**:
```bash
   alembic upgrade head --sql > migration.sql
   ```

4. **Migration Process**:
   - Update models in `api/models`
   - Update database connection in `alembic.ini`
   - Generate revision
   - Apply migrations
   - Create SQL file for deployment

---

## 🔄 **CI/CD Pipeline**

Managed via GitLab CI:

- ***Docker Stage***: Builds Docker images automatically using Kaniko.
- ***Delivery Stage***: Deploys Docker images automatically to Artifactory.
- ***Database Stage***: Handles database migrations and updates.

These stages execute automatically when a new Git tag is created.

---

## ⚙️ **API Configuration via Endpoint**

The API server can be configured through the `/configure` endpoint. This endpoint accepts a POST request with a JSON payload containing the complete system configuration.

### Configuration Payload Structure

The payload consists of several main components. The table below details the fields within each component:

**1. Global Parameters (`global_parameters`)**

| Field Name                | Type         | Required | Default Value | Description/Constraints |
| ------------------------- | ------------ | -------- | ------------- | ----------------------- |
| `mode`                    | Enum (Mode)  | No       | `online`      | System operation mode (`online` or `offline`) |
| `tmp_prefix`              | string | No       | `'.'`        | Prefix for temporary files during transfer |
| `final_prefix`            | string / null| No       | `null`        | Prefix for final files after transfer |
| `retry_delay`             | int          | No      | `300`        | Delay between retries in seconds |
| `max_retry`               | int          | No      | `5`           | Maximum number of retries |
| `transfer_requests_history`| int          | No      | `31`          | Retention period for requests in days |
| `only_new_data`           | boolean      | No      | `true`        | Transfer only new files globally |
| `transfer_timeout`        | int          | No      | `3600`         | Timeout for transfers in seconds |
| `queue_timeout`           | int          | No      | `86400`       | Timeout for requests in queue in seconds |
| `polling_interval`        | int          | No      | `10`          | Interval for polling in seconds |
| `queue_limit`             | int          | No      | `100`         | Maximum number of items in a queue |
| `queue_threshold`         | int          | No      | `80`          | Queue threshold percentage |

**2. Notification Servers (`notification_servers`)** - List of servers

| Field Name      | Type                  | Required | Default Value | Description/Constraints |
| --------------- | --------------------- | -------- | ------------- | ----------------------- |
| `name`          | string                | Yes      | -             | Unique server name |
| `type`          | Literal["kafka"]    | Yes      | -             | Server type (currently only "kafka") |
| `host`          | string                | Yes      | -             | Server host address |
| `port`          | int                   | Yes      | -             | Server port number |
| `timeout`       | int / null            | No       | `40`          | Connection timeout in seconds |
| `credentials`   | object / null         | No       | `null`        | Credentials object (see below) |

**Credentials Object (`credentials`)**

| Field Name | Type   | Required | Default Value | Description/Constraints |
| ---------- | ------ | -------- | ------------- | ----------------------- |
| `login`    | string | Yes      | -             | Username for authentication |
| `password` | string | Yes      | -             | Password for authentication |

**3. Queues (`queues`)** - List of queues

| Field Name        | Type       | Required | Default Value | Description/Constraints |
| ----------------- | ---------- | -------- | ------------- | ----------------------- |
| `name`            | string     | Yes      | -             | Unique queue name |
| `priority`        | int        | No       | `1`           | Queue priority (lower is higher) |
| `queue_timeout`   | int / null | No       | `86400`         | Timeout for items in this queue |
| `queue_limit`     | int / null | No       | `100`         | Max items for this queue |
| `queue_threshold` | int / null | No       | `80`          | Threshold percentage for this queue |

**4. Targets (`targets`)** - List of targets

| Field Name    | Type                   | Required | Default Value | Description/Constraints |
| ------------- | ---------------------- | -------- | ------------- | ----------------------- |
| `name`        | string                 | Yes      | -             | Unique target name |
| `protocol`    | Enum (Protocol)        | Yes      | -             | SFTP, FTP, FTPS, HTTP, HTTPS, S3 |
| `port`        | int                    | Yes      | -             | Target port number |
| `host`        | string                 | Yes      | -             | Target host address |
| `credentials` | object / null          | No       | `null`        | Credentials object |
| `parameters`  | object                 | No       | see below     | Target-specific parameters |

**Target Parameters Object (`parameters`)**

| Field Name | Type    | Required | Default Value | Description/Constraints |
| ---------- | ------- | -------- | ------------- | ----------------------- |
| `use_ssl`  | boolean | No       | `true`        | Use SSL for connection |
| `verify`   | boolean | No       | `true`        | Verify SSL certificate |

**5. Transfer Policies (`transfer_policies`)** - List of policies

| Field Name   | Type            | Required | Default Value | Description/Constraints |
| ------------ | --------------- | -------- | ------------- | ----------------------- |
| `name`       | string          | Yes      | -             | Unique policy name |
| `enabled`    | boolean         | No       | `true`        | Enable/disable policy |
| `type`       | Enum (Type)     | No      | `periodical`  | periodical, commanded |
| `src`        | object          | Yes      | -             | Source policy object (see below) |
| `dests`      | list[object]    | Yes      | -             | List of Destination policy objects (see below) |
| `queue`      | string          | Yes      | -             | Name of the queue to use |
| `parameters` | object / null   | No       | `null`        | Policy-specific parameters (see below) |

**Source Policy Object (`src`)**

| Field Name | Type           | Required | Default Value | Description/Constraints |
| ---------- | -------------- | -------- | ------------- | ----------------------- |
| `target`   | string         | Yes      | -             | Name of the target to use |
| `purge`    | boolean / null | No       | `false`       | Delete source files after transfer |
| `path`     | string / null  | No       | `null`        | Path on the source target |
| `bucket`   | string / null  | No       | `null`        | Bucket name (for S3) |
| `pattern`  | string         | Yes      | -             | File matching pattern |

**Destination Policy Object (`dests`)** - Contained in a list

| Field Name      | Type            | Required | Default Value | Description/Constraints |
| --------------- | --------------- | -------- | ------------- | ----------------------- |
| `target`        | string          | Yes      | -             | Name of the target to use |
| `path`          | string / null   | No       | `null`        | Path on the destination target |
| `bucket`        | string / null   | No       | `null`        | Bucket name (required for S3) |
| `tmp_prefix`    | string / null   | No       | `null`        | Temporary file prefix |
| `final_prefix`  | string / null   | No       | `null`        | Final file prefix |
| `path_from_filename_delimiter` | string / null | No | `null` | Delimiter character for dynamic path expressions (e.g., "$"). |
| `path_from_filename_expression`| list[string] / null | No | `null` | List of expressions to build the path (e.g., ["$\\d{4}[0]", "/", "$\\d{2}[1]"]). |
| `notifications` | list[object]/null| No      | `null`        | List of Notification objects (see below) |

**Dynamic Destination Path Generation**

The system supports the creation of dynamic destination subdirectories by parsing the source filename. This feature allows for advanced file organization based on information embedded in filenames, such as dates, version numbers, or data types.

The feature is activated on a specific destination policy by providing both `path_from_filename_delimiter` and `path_from_filename_expression`. If either of these fields is missing or empty, the dynamic path logic is skipped, and the standard destination `path` is used.

-   **`path_from_filename_delimiter`**: A single character (e.g., `$`) used to identify which parts of the expression list are dynamic regex patterns.
-   **`path_from_filename_expression`**: A list of strings that are concatenated to form the new relative path. This list can contain:
    -   **Literals**: Static path components, such as `archive` or `/`.
    -   **Expressions**: Strings that must begin with the specified `delimiter`. The format is `DELIMITER<regex>[group_index]`. The system will execute the `<regex>` on the filename and extract the match corresponding to the `[group_index]` (0-indexed).

***Example Scenario:***

Let's assume we want to organize incoming files into a `YYYY/DD` folder structure based on their filename.

-   **Source Filename**: `R_MOC_DATA_PNEO3_00_2024-07-15T10-00-00-000.xml`
-   **Base Destination Path (`path`)**: `/data/ingest`
-   **Configuration**:
    -   `path_from_filename_delimiter`: `$`
    -   `path_from_filename_expression`: [`$\\d{4}[0]`, `/`, `$\\d{2}[3]`]

***Path Generation Breakdown:***

1.  The worker processes the `path_from_filename_expression` list item by item:
2.  `$\\d{4}[0]`:
    -   It starts with `$`, so it's a dynamic expression.
    -   The regex `\\d{4}` is executed on the filename.
    -   The first match (`[0]`) is `2024`.
    -   *Resulting path so far: `2024`*
3.  `/`:
    -   This does not start with `$`, so it's treated as a literal string.
    -   *Resulting path so far: `2024/`*
4.  `$\\d{2}[3]`:
    -   It starts with `$`, so it's a dynamic expression.
    -   The regex `\\d{2}` is executed on the filename. This finds multiple matches: `00`, `20`, `24`, `07`, `15`, `10`, etc.
    -   The fourth match (`[3]`) is `07`.
    -   *Resulting path so far: `2024/07`*

***Final Result:***

The generated relative path `2024/07` is appended to the policy's base path, and the file is uploaded to the final, fully constructed path:
`/data/ingest/2024/07/R_MOC_DATA_PNEO3_00_2024-07-15T10-00-00-000.xml`

**Notification Object (`notifications`)** - Contained in a list within `dests`

| Field Name   | Type   | Required | Default Value | Description/Constraints |
| ------------ | ------ | -------- | ------------- | ----------------------- |
| `server`     | string | Yes      | -             | Name of the notification server |
| `topic`      | string | Yes      | -             | Kafka topic name (if type is Kafka) |
| `replica`    | int    | No       | `1`           | Kafka replica count |
| `partitions` | int    | No       | `1`           | Kafka partition count |
| `...`        | any    | No       | -             | Other server-specific parameters |

**Policy Parameters Object (`parameters`)**

| Field Name                | Type            | Required | Default Value | Description/Constraints |
| ------------------------- | --------------- | -------- | ------------- | ----------------------- |
| `only_new_data`           | boolean / null  | No       | `null`        | Override global `only_new_data` |
| `max_retry`               | int / null      | No       | `null`        | Override global `max_retry` |
| `retry_delay`             | int / null      | No       | `null`        | Override global `retry_delay` |
| `transfer_requests_history`| int / null     | No       | `null`        | Override global history setting |
| `transfer_timeout`        | int / null      | No       | `null`        | Override global transfer timeout |
| `periodical`              | object / null   | No       | `null`        | Parameters for periodical policies |

**Periodical Parameters Object (`periodical`)**

| Field Name         | Type       | Required | Default Value | Description/Constraints |
| ------------------ | ---------- | -------- | ------------- | ----------------------- |
| `polling_interval` | int / null | No       | `null`        | Override global polling interval |


### Validation Rules

1. **Unique Names**: Target, Policy, Queue, and Server names must be unique across their respective lists.
2. **Reference Integrity**: Policy source/destination targets must refer to existing targets by name. Policy queue must refer to an existing queue by name. Destination notifications must refer to existing servers by name.
3. **Type Constraints**: Ensure `protocol`, `type` (server), and `type` (policy) fields use allowed enum/literal values.

### Example Configuration

```bash
# POST /configure
curl -X POST http://localhost:9000/configure \
  -H "Content-Type: application/json" \
  -d '{
    "global_parameters": {
      "mode": "ONLINE",
      "retry_delay": 3600,
      "max_retry": 5,
      "transfer_requests_history": 31,
      "only_new_data": true,
      "transfer_timeout": 300,
      "queue_timeout": 86400,
      "polling_interval": 10,
      "queue_limit": 100,
      "queue_threshold": 80
    },
    "notification_servers": [
      {
        "name": "kafka-prod",
        "type": "kafka",
        "host": "kafka.example.com",
        "port": 9092,
        "credentials": {
          "login": "user",
          "password": "pass"
        }
      }
    ],
    "queues": [
      {
        "name": "high-priority",
        "priority": 1
      }
    ],
    "targets": [
      {
        "name": "source-sftp",
        "protocol": "SFTP",
        "host": "sftp.example.com",
        "port": 22,
        "credentials": {
          "login": "user",
          "password": "pass"
        }
      }
    ],
    "transfer_policies": [
      {
        "name": "daily-backup",
        "type": "PERIODICAL",
        "src": {
          "target": "source-sftp",
          "path": "/data",
          "pattern": "*.log"
        },
        "dests": [
          {
            "target": "source-sftp",
            "path": "/backup",
            "notifications": [
               {
                 "server": "kafka-prod",
                 "topic": "dtr-notifications"
               }
            ]
          }
        ],
        "queue": "high-priority"
      }
    ]
  }'
```

### Error Handling

The configuration endpoint will return:
- 201: Configuration successfully applied
- 400: Invalid configuration (with detailed error message)
- 500: Server error (with stack trace in debug mode)

---

## 👤 **User-Facing API Endpoints**

These endpoints are intended for end-users or external systems interacting with the DTR.

### 1. Get Transfer Status (`GET /get-status`)

Retrieves the detailed status and information for a specific transfer request using its unique transfer ID (UUID).

**Query Parameters:**

| Parameter   | Type   | Required | Description                     |
| ----------- | ------ | -------- | ------------------------------- |
| `id`        | string | Yes      | The UUID of the transfer request |

**Example Request:**

```bash
curl -X GET "http://localhost:9000/dtr/v1/get-status?id=a1b2c3d4-e5f6-7890-1234-567890abcdef"
```

**Example Success Response (200 OK):**

```json
{
  "follows_from_task": "task-uuid-if-any",
  "transfer_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "transfer_status": {
    "status": "SUCCESSFUL",
    "sub_status": "NOTIFY",
    "failure_count": 0,
    "failure_reason": null
  },
  "transfer_info": {
    "data_identifier": "important_data.zip",
    "data_size_mb": 1024.5,
    "data_type": "file",
    "policy_name": "backup-policy",
    "created_at": "2023-10-27T10:00:00+00:00",
    "transfer_begin_time": "2023-10-27T10:05:00+00:00",
    "transfer_end_time": "2023-10-27T10:15:00+00:00",
    "transfer_rate_mb_s": 1.71
  },
  "download": {
    "source": {
      "name": "source-sftp",
      "path": "/data/outgoing",
      "protocol": "SFTP"
    },
    "download_rate_mb_s": 2.0,
    "download_time_s": 512.25
  },
  "upload": {
    "destination": {
      "name": "destination-s3",
      "path": "/backups",
      "protocol": "S3"
    },
    "upload_rate_mb_s": 1.5,
    "upload_time_s": 683.0
  }
}
```

**Example Error Response (404 Not Found):**

```json
{
  "error": "Transfer request not found"
}
```

### 2. Create Commanded Transfer Request (`POST /transfer-request`)

Initiates a new data transfer based on an existing "COMMANDED" type transfer policy. This is used for on-demand transfers.

**Request Body:**

| Field             | Type             | Required | Description |
| ----------------- | ---------------- | -------- | ----------- |
| `transfer_policy` | string           | Yes      | Name of the existing COMMANDED transfer policy to use |
| `path`            | string           | Yes      | Full path or URL to the source file/resource |
| `uid`             | string (UUID) / null | No       | Optional UUID to link this request to an external task |
| `timestamp`       | string (ISO 8601) / null | No   | Optional timestamp for the request |

**Example Request Payload:**

```json
{
  "transfer_policy": "manual-file-push",
  "path": "/local/path/to/myfile.dat",
  "uid": "b2c3d4e5-f6a7-8901-2345-67890abcdef0"
}
```

**Example Request with URL:**

```json
{
  "transfer_policy": "manual-http-download",
  "path": "https://example.com/files/report.pdf"
}
```

**Example Success Response (200 OK):**

```json
{
  "transfer_id": [
    "c3d4e5f6-a7b8-9012-3456-7890abcdef01",
    "d4e5f6a7-b8c9-0123-4567-890abcdef012" 
  ]
}
```
*(Note: Returns a list of transfer IDs, one for each destination defined in the policy)*

**Example Error Response (404 Not Found):**

```json
{
  "error": "Transfer policy 'manual-file-push' not found or is not a commanded policy"
}
```

**Example Error Response (400 Bad Request):**

```json
{
  "error": "No destinations configured for policy 'manual-file-push'"
}
```

**Example Error Response (409 Conflict):**

```json
{
  "error": "No new transfers could be created - all destinations have transfers in progress"
}
```

---
