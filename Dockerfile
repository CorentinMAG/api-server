FROM aforge-frdr.biz.nstd.fr.airbusds.corp/gw_registry-1_docker_io_4dev/python:3.10.13-alpine3.18

ARG AFORGE_HOST \
    AFORGE_PASSWORD \
    AFORGE_USER \
    AFORGE_PIP_REPO \
	AFORGE_ALPINE_REPO \
    DOCKER_TAG

ENV DTR_DB_NAME=dtr \
    DTR_DB_USER=** \
    DTR_DB_PASSWORD=** \
    DTR_DB_HOST=localhost \
    DTR_DB_PORT=5432 \
    DTR_API_VERSION=$DOCKER_TAG \
    DTR_DB_CREATE=false

WORKDIR /opt/api

ENV PIP_CONFIG_FILE=/etc/pip.conf

RUN echo "https://${AFORGE_USER}:${AFORGE_PASSWORD}@$AFORGE_HOST/artifactory/${AFORGE_ALPINE_REPO}/main" > /etc/apk/repositories && \
    echo "https://${AFORGE_USER}:${AFORGE_PASSWORD}@$AFORGE_HOST/artifactory/${AFORGE_ALPINE_REPO}/community" >> /etc/apk/repositories

RUN apk --no-check-certificate update && \
    apk --no-check-certificate add \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev && \
    rm /etc/apk/repositories

RUN echo "[global]" > /etc/pip.conf && \
	echo "index-url = https://${AFORGE_USER}:${AFORGE_PASSWORD}@${AFORGE_HOST}/artifactory/api/pypi/${AFORGE_PIP_REPO}/simple" >> /etc/pip.conf && \
	echo "trusted-host = ${AFORGE_HOST}" >> /etc/pip.conf

COPY ./ ./

RUN pip3 install -r requirements.txt && rm /etc/pip.conf
RUN chmod -R +x ./scripts

ENTRYPOINT ["/opt/api/scripts/docker-entrypoint.sh"]