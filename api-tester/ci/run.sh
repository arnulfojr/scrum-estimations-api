#!/bin/sh

DOCKER_COMPOSE='docker-compose -f docker-compose.yml -f docker/docker-compose.tester.yml'

set -e

echo '--- Running tester container'

set +e
${DOCKER_COMPOSE} run --use-aliases tester /app/tests
EXIT_CODE=${?}
set -e

if [ "${EXIT_CODE}" -eq '0' ]; then
  echo '--- All good'
else
  echo "--- Tests failed with code ${EXIT_CODE}"
  ${DOCKER_COMPOSE} logs server > api-tester/out/server.log
  ${DOCKER_COMPOSE} logs tester > api-tester/out/tester.log
fi

# exit with original exit code
exit ${EXIT_CODE}
