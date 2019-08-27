#!/usr/bin/env sh

set -e

if [ -z "${DOCKER_NETWORK_ID}" ]; then
  if [ -z "${DOCKER_NETWORK_NAME}" ]; then
    # we generate a uuid based on time so we can somehow control the network names
    DOCKER_NETWORK_NAME="$(uuidgen)"
    echo "--- DOCKER_NETWORK_NAME was not given, defaulting to ${DOCKER_NETWORK_NAME}"
  fi
  export DOCKER_NETWORK_NAME

  # shellcheck disable=SC2086
  DOCKER_NETWORK_ID="$(docker network ls --filter=name="${DOCKER_NETWORK_NAME}" --format='{{.ID}}')"

  if [ -z "${DOCKER_NETWORK_ID}" ]; then
    # shellcheck disable=SC2086
    DOCKER_NETWORK_ID="$(docker network create "${DOCKER_NETWORK_NAME}")"
    echo "------ Network not found, created ${DOCKER_NETWORK_NAME}"
  fi
  export DOCKER_NETWORK_ID
fi
echo "--- DOCKER_NETWORK_ID set to '${DOCKER_NETWORK_ID}'"

# fire up the database, if not found
set +e
docker run --network="${DOCKER_NETWORK_ID}" \
           --rm jwilder/dockerize -wait tcp://db:3306 --timeout 5s
CHECK_CODE="${?}"
set -e

DB_CONTAINER_ID=
if [ "${CHECK_CODE}" = '1' ]; then
  echo '--- Booting the database in background'
  DB_CONTAINER_ID="$(docker run --rm --detach \
                                --network="${DOCKER_NETWORK_ID}" \
                                --network-alias=db \
                                --env-file="${PWD}/env.d/db.env" \
                                --env-file="${PWD}/env.d/app.db.env" \
                                mysql:5.7)"
  echo '--- Ok, will now wait for the database to have an open TCP socket'
  set +e
  docker run --network="${DOCKER_NETWORK_ID}" \
             --rm jwilder/dockerize -wait tcp://db:3306 --timeout 30s
  EXIT_CODE=${?}
  set -e

  if [ "${EXIT_CODE}" -eq '1' ]; then
    echo '!!! We failed to wait for the database, cleaning up...'
    docker stop "${DB_CONTAINER_ID}" || true
    docker rm "${DB_CONTAINER_ID}" || true
    exit ${EXIT_CODE}
  fi
else
  echo '--- Database was found wont create'
fi
export DB_CONTAINER_ID
