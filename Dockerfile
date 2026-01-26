FROM aforge-frdr.biz.nstd.fr.airbusds.corp/gw_registry-1_docker_io_4dev/python:3.10.13-alpine3.18 AS builder

ARG AFORGE_HOST \
    AFORGE_PASSWORD \
    AFORGE_USER \
    AFORGE_PIP_REPO \
	AFORGE_ALPINE_REPO \
    DOCKER_TAG \
    AFORGE_PIP_DTR

WORKDIR /builder

ENV PIP_CONFIG_FILE=/etc/pip.conf

RUN echo "[global]" > /etc/pip.conf && \
	echo "index-url = https://${AFORGE_USER}:${AFORGE_PASSWORD}@${AFORGE_HOST}/artifactory/api/pypi/${AFORGE_PIP_REPO}/simple" >> /etc/pip.conf && \
    echo "extra-index-url = https://${AFORGE_USER}:${AFORGE_PASSWORD}@${AFORGE_HOST}/artifactory/api/pypi/${AFORGE_PIP_DTR}/simple" >> /etc/pip.conf && \ 
	echo "cert = ${CA_BUNDLE_PATH}" >> /etc/pip.conf

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt \
    && rm /etc/pip.conf

COPY ./ ./app

FROM aforge-frdr.biz.nstd.fr.airbusds.corp/gw_registry-1_docker_io_4dev/python:3.10.13-alpine3.18

ENV DTR_DB_NAME=dtr \
    DTR_DB_USER=** \
    DTR_DB_PASSWORD=** \
    DTR_DB_HOST=localhost \
    DTR_DB_PORT=5432 \
    DTR_API_VERSION=$DOCKER_TAG \
    DTR_VERSION=$DOCKER_TAG \
    DTR_DB_CREATE=false \
    DTR_LOG_LEVEL=INFO

RUN addgroup -S dtrgroup \
    && adduser -S dtruser -G dtrgroup
WORKDIR /app
RUN chown dtruser:dtrgroup /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=dtruser:dtrgroup --from=builder /builder/app/ /app
USER dtruser
RUN chmod +x ./scripts/docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]