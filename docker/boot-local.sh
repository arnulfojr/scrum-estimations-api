#!/bin/sh

DOCKER_COMPOSE='docker-compose -f docker-compose.yml -f docker/docker-compose.local.yml'

set -e

if [ -z "${DOCKER_NETWORK_NAME}" ]; then
  export DOCKER_NETWORK_NAME='scrum-apis'
  echo "--- DOCKER_NETWORK_NAME was not given, defaulting to ${DOCKER_NETWORK_NAME}"
fi

# shellcheck disable=SC2086
DOCKER_NETWORK_ID="$(docker network ls --filter=name="${DOCKER_NETWORK_NAME}" --format='{{.ID}}')"
if [ -z "${DOCKER_NETWORK_ID}" ]; then
  # shellcheck disable=SC2086
  DOCKER_NETWORK_ID="$(docker network create "${DOCKER_NETWORK_NAME}")"
  echo "------ Network not found, created ${DOCKER_NETWORK_NAME}"
fi
echo "--- DOCKER_NETWORK_ID set to '${DOCKER_NETWORK_ID}'"

# fire up the database
echo '--- Booting the database in background'
${DOCKER_COMPOSE} up -d db

echo '--- Ok, will now wait for the database to have an open TCP socket'
set +e
docker run --network="${DOCKER_NETWORK_ID}" --rm jwilder/dockerize -wait tcp://db:3306 --timeout 20s
EXIT_CODE=${?}
set -e

if [ "${EXIT_CODE}" -eq '1' ]; then
  echo '!!! We failed to wait for the database, cleaning up...'
  ${DOCKER_COMPOSE} down -v
  exit ${EXIT_CODE}
fi

# now we run "safely"
${DOCKER_COMPOSE} up
