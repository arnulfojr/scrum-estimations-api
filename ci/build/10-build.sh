#!/usr/bin/env sh

set -e

assert_vars_exists REPO_NAME ARTIFACT_TAG PROJECT_NAME

docker build --tag "${REPO_NAME}":"${ARTIFACT_TAG}" \
             --no-cache \
             --label="Project=${PROJECT_NAME}" .
