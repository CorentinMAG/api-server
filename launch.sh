#!/bin/bash

export DTR_DB_USER=postgres;
export DTR_DB_PASSWORD=postgres;
export DTR_DB_CREATE=true;
export DTR_DB_PORT=5438;
export DTR_DB_NAME=dtr;
export DTR_LOG_LEVEL=DEBUG;
export DTR_ENCRYPTION_KEY=azeaze;
flask --app api run --debug --port 5000 --host 0.0.0.0