# Api Server module

## Set up tools

```bash
$ pip install -r requirements-dev.txt
$ pip install -r requirements.txt
$ pre-commit install
```

Now, when you commit your files the linter/formatter pipeline will be executed

## Environment variables

| name | description | default value |
|------|-------------|---------------|
| **DTR_DB_NAME** | database name | `dtr` |
| **DTR_DB_USER** | database user | `postgres` |
| **DTR_DB_PASSWORD** | database user password | `N/A` |
| **DTR_DB_HOST** | database host | `127.0.0.1` |
| **DTR_DB_PORT** | database port | `5432` |
| **DTR_DB_CREATE** | wether to create the database schema or not | `false` |
| **DTR_API_VERSION** | API version | `$DOCKER_TAG` (generated when the docker image is built) |
| **DTR_LOG_LEVEL** | the log level| `INFO` |

## start in local environment

1. create virtual environment
```bash
$ python3 -m venv ~/Envs/dtr/api
$ source ~/Envs/dtr/api/bin/activate
$ pip install -r requirements.txt -r requirements-dev.txt
$ pip install -r api/common/requirements.txt
$ deactivate
``` 

2. run the api
```bash
$ source ~/Envs/dtr/api/bin/activate
$ export DTR_DB_NAME=...
## define all environment variables
$ flask --app api run --debug # set the debug flag if you want hot reload
```

```
$ export DTR_DB_NAME=...
# define all above variables
$ flask run --app api --debug
```

## start in docker

```bash
$ docker build -t api-server \
> --build-arg AFORGE_HOST=... \
> --build-arg AFORGE_USER=... \
> --build-arg AFORGE_PASSWORD=... \
> --build-arg AFORGE_ALPINE_REPO=... \
> --build-arg AFORGE_PIP_REPO=... \
> --build-arg DOCKER_TAG=... \
> .

$ docker run -dp 80:80 api-server
```

## start in docker-compose

check out the `dtr/dtr` repository

## update models

1. update your models in `api/models`
2. update database connection in `alembic.ini` (`sqlalchemy.url`)
3. generate the revision `alembic revision --autogenerate -m "xxx"`
4. apply the migrations `alembic upgrade head`
5. create the new sql file `alembic upgrade head --sql > ../dtr/db/dtr-xxx.sql`


## run alembic to generate migrations

1. create the migration
```bash
$ alembic revision -m "my first revision"
```

2. run the latest migration (create table in database)
```bash
$ alembic upgrade head
```

3. generate the sql script
```bash
$ alembic upgrade <revision> --sql > my_file.sql
```

