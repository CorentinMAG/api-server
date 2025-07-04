FROM aforge-frdr.biz.nstd.fr.airbusds.corp/gw_registry-1_docker_io_4dev/python:3.10.13-alpine3.18

ARG AFORGE_HOST \
    AFORGE_PASSWORD \
    AFORGE_USER \
    AFORGE_PIP_REPO \
	AFORGE_ALPINE_REPO \
    DOCKER_TAG \
    AFORGE_PIP_DTR

ENV DTR_DB_NAME=dtr \
    DTR_DB_USER=** \
    DTR_DB_PASSWORD=** \
    DTR_DB_HOST=localhost \
    DTR_DB_PORT=5432 \
    DTR_API_VERSION=$DOCKER_TAG \
    DTR_VERSION=$DOCKER_TAG \
    DTR_DB_CREATE=false \
    DTR_LOG_LEVEL=INFO

WORKDIR /opt/api

ENV PIP_CONFIG_FILE=/etc/pip.conf

RUN echo "https://${AFORGE_USER}:${AFORGE_PASSWORD}@$AFORGE_HOST/artifactory/${AFORGE_ALPINE_REPO}/main" > /etc/apk/repositories && \
    echo "https://${AFORGE_USER}:${AFORGE_PASSWORD}@$AFORGE_HOST/artifactory/${AFORGE_ALPINE_REPO}/community" >> /etc/apk/repositories

RUN apk --no-check-certificate update && \
    apk --no-check-certificate add \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    curl \
    netcat-openbsd && \
    rm /etc/apk/repositories

RUN echo "[global]" > /etc/pip.conf && \
	echo "index-url = https://${AFORGE_USER}:${AFORGE_PASSWORD}@${AFORGE_HOST}/artifactory/api/pypi/${AFORGE_PIP_REPO}/simple" >> /etc/pip.conf && \
    echo "extra-index-url = https://${AFORGE_USER}:${AFORGE_PASSWORD}@${AFORGE_HOST}/artifactory/api/pypi/${AFORGE_PIP_DTR}/simple" >> /etc/pip.conf && \ 
	echo "trusted-host = ${AFORGE_HOST}" >> /etc/pip.conf

COPY ./ ./

RUN pip3 install -r requirements.txt && rm /etc/pip.conf
RUN chmod -R +x ./scripts

# Health check for Kubernetes/Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:80/healthz || exit 1

# Use non-root user for security
RUN addgroup -g 1000 dtr && \
    adduser -u 1000 -G dtr -s /bin/sh -D dtr && \
    chown -R dtr:dtr /opt/api

USER dtr

EXPOSE 80

ENTRYPOINT ["/opt/api/scripts/docker-entrypoint.sh"]