#!/bin/bash

export DTR_ENV=development
export DTR_API_VERSION=3.0.0-dev
export DTR_VERSION=3.0.0-dev
export DTR_LOG_LEVEL=DEBUG

export DTR_DB_USER=postgres;
export DTR_DB_PASSWORD=postgres;
export DTR_DB_NAME=dtr;
export DTR_DB_HOST=127.0.0.1
export DTR_DB_PORT=5438;
export DTR_DB_CREATE=true;
export DTR_ENCRYPTION_KEY=azeaze;

# activate venv
source ~/Envs/dtr/api/bin/activate && \
  flask --app api run --debug --port 5000 --host 0.0.0.0