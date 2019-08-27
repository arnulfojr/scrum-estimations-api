#!/usr/bin/env sh

set -e

assert_vars_exists DOCKER_USERNAME DOCKER_PASSWORD

echo "${DOCKER_PASSWORD}" | docker login --username "${DOCKER_USERNAME}" --password-stdin
