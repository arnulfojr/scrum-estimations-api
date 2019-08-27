#!/usr/bin/env sh

set -e

assert_vars_exists DOCKER_NETWORK_ID PROJECT_DIRECTORY REPO_NAME ARTIFACT_TAG

echo '------ Creating schema/database'
docker run --rm --network="${DOCKER_NETWORK_ID}" \
           --env-file="${PROJECT_DIRECTORY}/env.d/app.env" \
           --env-file="${PROJECT_DIRECTORY}/env.d/app.db.env" \
           --label=Project="${PROJECT_NAME}" \
           "${REPO_NAME}":"${ARTIFACT_TAG}" create-db

echo '------ Running migrations'
docker run --rm --network="${DOCKER_NETWORK_ID}" \
           --env-file="${PROJECT_DIRECTORY}/env.d/app.env" \
           --env-file="${PROJECT_DIRECTORY}/env.d/app.db.env" \
           --label=Project="${PROJECT_NAME}" \
           "${REPO_NAME}":"${ARTIFACT_TAG}" migrate
