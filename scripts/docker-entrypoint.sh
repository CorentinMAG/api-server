#!bin/sh

if [ "$DTR_DB_USER" = "**" ]; then
  echo "You must set the DTR_DB_USER variable!"
  exit 1;
fi

if [ "$DTR_DB_PASSWORD" = "**" ]; then
  echo "You must set the DTR_DB_PASSWORD variable!"
  exit 1;
fi

gunicorn \
  --bind=0.0.0.0:80 \
  'api:create_app()'

