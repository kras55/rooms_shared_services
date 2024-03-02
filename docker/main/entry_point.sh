#!/bin/sh
if [ ! -z "${UNIT_TEST}" ]; then
  echo "Starting unit tests ..."
  exec /usr/local/bin/python -m pytest -vv tests/unit
elif [ ! -z "${INTEGRATION_TEST}" ]; then
  echo "Starting integration tests ..."
  exec /usr/local/bin/python -m pytest -vv tests/integration -k test_pagination
else
  exec /usr/local/bin/python -m rooms_shared_services.src.main
fi
