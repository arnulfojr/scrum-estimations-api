#!/usr/bin/env sh

set -e

echo '------ Creating schema/database'
docker run --rm --network="${DOCKER_NETWORK_ID}" \
           --env-file="${PWD}/env.d/app.env" \
           --env-file="${PWD}/env.d/app.db.env" \
           --label=Project=Estimations \
           "${DOCKER_IMAGE_NAME}":"${DOCKER_IMAGE_TAG}" create-db

echo '------ Running migrations'
docker run --rm --network="${DOCKER_NETWORK_ID}" \
           --env-file="${PWD}/env.d/app.env" \
           --env-file="${PWD}/env.d/app.db.env" \
           --label=Project=Estimations \
           "${DOCKER_IMAGE_NAME}":"${DOCKER_IMAGE_TAG}" migrate
