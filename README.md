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
| **DTR_DB_NAME**| database name | `N/A` |
| **DTR_DB_USER**| database user | `N/A` |
| **DTR_DB_PASSWORD**| database user password | `N/A` |
| **DTR_DB_HOST**| database host | `localhost` |
| **DTR_DB_PORT**| database port | `5432` |
| **DTR_DB_CREATE**| wether to create the database schema or not | `false` |
|**DTR_API_VERSION**| API version | `$DOCKER_TAG` (generated when the docker image is built) |

## start in local environment

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