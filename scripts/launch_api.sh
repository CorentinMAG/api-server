#!/bin/bash

source ~/Envs/dtr/api/bin/activate

# define all environment variables
export DTR_DB_NAME=dtr
export DTR_API_VERSION=1.1.8
export DTR_DB_USER=postgres
export DTR_DB_PASSWORD=test
export DTR_DB_HOST=localhost
export DTR_DB_PORT=5438
export DTR_DB_CREATE=true
export DTR_LOG_LEVEL=INFO



flask --app api run --debug # set the debug flag if you want hot reload