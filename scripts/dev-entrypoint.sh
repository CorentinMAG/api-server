#!/bin/sh

if [ "$DTR_DB_USER" = "**" ]; then
  echo "You must set the DTR_DB_USER variable!"
  exit 1;
fi

if [ "$DTR_DB_PASSWORD" = "**" ]; then
  echo "You must set the DTR_DB_PASSWORD variable!"
  exit 1;
fi

flask --app api run --debug --port 80 --host 0.0.0.0