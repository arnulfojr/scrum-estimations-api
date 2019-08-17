#!/bin/sh

set -e

if [ "${1}" = 'develop' ]; then
  pip install --disable-pip-version-check \
              -r "${APP_DIR}"/requirements-dev.txt
  exec flask run --host "${HOSTNAME}" --port "${PORT}"
fi

if [ "${1}" = 'migrate' ]; then
  create-db
  exec migrate
fi

if [ "${1}" = 'revert' ]; then
  exec revert
fi

if [ "${1}" = 'serve' ]; then
  exec gunicorn -c "${APP_DIR}"/conf/app_conf.py run:app
fi

echo "Unmatched command, executing: $*"
exec "${@}"
