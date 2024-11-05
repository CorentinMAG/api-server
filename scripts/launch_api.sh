#!/bin/bash

# define all environment variables
export DTR_API_SERVER=http://127.0.0.1:5000
#export DTR_CERT_PATH=/home/pfi.access.poleos.lan/acruzel/certificates/dtr


source ~/Envs/dtr/api/bin/activate

# define all environment variables
export DTR_DB_NAME=dtr
export DTR_API_VERSION=2.0.0-rc.1
export DTR_DB_USER=postgres
export DTR_DB_PASSWORD=vlgklm91810
export DTR_DB_HOST=127.0.0.1
export DTR_DB_PORT=5438
export DTR_DB_CREATE=true
export DTR_LOG_LEVEL=DEBUG
export DTR_ENCRYPTION_KEY=azeaze
export DTR_VERSION=2.0.1



flask --app api run --debug # set the debug flag if you want hot reload