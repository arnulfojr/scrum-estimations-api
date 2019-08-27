#!/usr/bin/env sh

set -e

assert_vars_exists REPO_NAME BRANCH_NAME ARTIFACT_TAG

if [ -z "${DOCKER_REPO_NAME}" ]; then
  DOCKER_REPO_NAME="${DOCKER_USERNAME}/${REPO_NAME}"
fi

docker push "${DOCKER_REPO_NAME}":"${ARTIFACT_TAG}"
docker push "${DOCKER_REPO_NAME}":"${BRANCH_NAME}"
