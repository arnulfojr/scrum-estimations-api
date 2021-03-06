#!/usr/bin/env sh

set -e

assert_vars_exists DOCKER_NETWORK_ID PROJECT_DIRECTORY REPO_NAME ARTIFACT_TAG

echo '--- Launching the server'
SERVER_CONTAINER_ID="$(docker run --rm --detach \
           --network="${DOCKER_NETWORK_ID}" \
           --network-alias=server \
           --env-file="${PROJECT_DIRECTORY}/env.d/app.env" \
           --env-file="${PROJECT_DIRECTORY}/env.d/app.db.env" \
           --label=Project="${PROJECT_NAME}" \
           "${REPO_NAME}":"${ARTIFACT_TAG}" serve)"
export SERVER_CONTAINER_ID

docker run --network="${DOCKER_NETWORK_ID}" \
           --rm jwilder/dockerize -wait http://server:5000/selfz/healthz --timeout 20s


echo '--- Running tester container'
docker build --tag tavern --label=Application=Tester ./api-tester

set +e
docker run --rm --network="${DOCKER_NETWORK_ID}" tavern /app/tests
EXIT_CODE=${?}
set -e
export EXIT_CODE

if [ "${EXIT_CODE}" -eq '0' ]; then
  echo '--- All good while testing'
else
  echo "--- Tests failed with code ${EXIT_CODE}"
fi
