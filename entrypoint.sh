#!/bin/sh

set -e

if [ "${1}" = 'develop' ]; then
  pip install --disable-pip-version-check \
              -r ${APP_DIR}/requirements-dev.txt
  exec adev runserver ${APP_DIR}/src/run.py --app-factory App
fi

if [ "${1}" = 'migrate' ]; then
  exec migrate
fi

if [ "${1}" = 'revert' ]; then
  exec revert
fi

if [ "${1}" = 'serve' ]; then
  exec python -m
fi

echo "Unmatched command, executing: ${@}"
exec ${@}
