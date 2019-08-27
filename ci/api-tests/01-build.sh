#!/usr/bin/env sh

set -e

assert_vars_exists REPO_NAME ARTIFACT_TAG

docker build --tag "${REPO_NAME}":"${ARTIFACT_TAG}" \
                                --label=Project=Estimations \
                                .
