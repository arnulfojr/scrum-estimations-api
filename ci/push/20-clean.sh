#!/usr/bin/env sh

set -e

if [ -z "${DOCKER_IMAGE_NAME}" ]; then
  DOCKER_IMAGE_NAME="${REPO_NAME}"
fi
export DOCKER_IMAGE_NAME

DOCKER_REPO_NAME="${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}"

if [ -z "${DOCKER_IMAGE_TAG}" ]; then
  DOCKER_IMAGE_TAG="${ARTIFACT_TAG}"
fi
export DOCKER_IMAGE_TAG

docker rmi "${DOCKER_REPO_NAME}":"${DOCKER_IMAGE_TAG}" || true
