#!/usr/bin/env sh

set -e

# clean up
docker stop "${SERVER_CONTAINER_ID}" || true
docker stop "${DB_CONTAINER_ID}" || true
docker network rm "${DOCKER_NETWORK_ID}" || true