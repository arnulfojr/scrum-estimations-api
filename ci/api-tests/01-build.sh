#!/usr/bin/env sh

set -e

DOCKER_IMAGE_NAME="${REPO_NAME}"
export DOCKER_IMAGE_NAME

DOCKER_IMAGE_TAG="${ARTIFACT_TAG}"
export DOCKER_IMAGE_TAG

docker build --tag "${DOCKER_IMAGE_NAME}":"${DOCKER_IMAGE_TAG}" \
                                --label=Project=Estimations \
                                .
