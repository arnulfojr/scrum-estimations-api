#!/bin/sh

DOCKER_COMPOSE='docker-compose -f docker-compose.yml -f docker/docker-compose.tester.yml'

set -e

if [ -z "${DOCKER_NETWORK_NAME}" ]; then
  export DOCKER_NETWORK_NAME='scrum-apis'
  echo "--- DOCKER_NETWORK_NAME was not given, defaulting to ${DOCKER_NETWORK_NAME}"
fi

# Wait for the db to boot
DOCKER_NETWORK_ID="$(docker network ls --filter=name=${DOCKER_NETWORK_NAME} --format='{{.ID}}')"
if [ -z "${DOCKER_NETWORK_ID}" ]; then
  DOCKER_NETWORK_ID=$(docker network create ${DOCKER_NETWORK_NAME})
  echo "------ Network not found, created ${DOCKER_NETWORK_NAME}"
fi
echo "--- DOCKER_NETWORK_ID set to '${DOCKER_NETWORK_ID}'"

# remove all the container and volumes, so we can have a clean state
echo '--- Sorry, we will clean up all the state'
${DOCKER_COMPOSE} down -v

# fire up the database
echo '--- Booting the database in background'
${DOCKER_COMPOSE} up -d db

echo '--- Ok, will now wait for the database to have an open TCP socket'
set +e
docker run --network=${DOCKER_NETWORK_ID} --rm jwilder/dockerize -wait tcp://db:3306 --timeout 20s
EXIT_CODE=${?}
set -e

if [ "${EXIT_CODE}" -eq '1' ]; then
  echo '!!! We failed to wait for the database, cleaning up...'
  ${DOCKER_COMPOSE} down -v
  exit ${EXIT_CODE}
fi

echo '--- Will run now migrations'

echo '------ Creating schema/database'
# create the database if not existing
${DOCKER_COMPOSE} run migrations create-db

echo '------ Running migrations'
# run the migrations
${DOCKER_COMPOSE} run migrations

echo '--- Finished prepating the set up'

echo '--- Launching the server'
${DOCKER_COMPOSE} run -d --use-aliases server

docker run --network=${DOCKER_NETWORK_ID} --rm jwilder/dockerize -wait http://server:5000/selfz/healthz --timeout 20s
