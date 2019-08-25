#!/usr/bin/env sh

set -e

# exit with original exit code
if [ -z "${EXIT_CODE}" ]; then
  exit 0
else
  echo "... a step set the EXIT_CODE to ${EXIT_CODE}"
  exit "${EXIT_CODE}"
fi
