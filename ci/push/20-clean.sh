#!/usr/bin/env sh

set -e

DOCKER_REPO_NAME="${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}"

docker rmi "${REPO_NAME}":"${ARTIFACT_TAG}" || true
docker rmi "${DOCKER_REPO_NAME}":"${ARTIFACT_TAG}" || true
