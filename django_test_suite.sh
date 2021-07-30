#!/bin/bash
# Copyright 2021 PingCAP, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# See the License for the specific language governing permissions and
# limitations under the License.

set -x pipefail

# Disable buffering, so that the logs stream through.
export PYTHONUNBUFFERED=1

export DJANGO_TESTS_DIR="django_tests_dir"
mkdir -p $DJANGO_TESTS_DIR

pip3 install .
git clone --depth 1  --branch "3.2.5" https://github.com/django/django.git $DJANGO_TESTS_DIR/django
cp tidb_settings.py $DJANGO_TESTS_DIR/django/tidb_settings.py

cd $DJANGO_TESTS_DIR/django && pip3 install -e . && pip3 install -r tests/requirements/py3.txt && pip3 install -r tests/requirements/mysql.txt; cd ../../

SETTINGS_FILE="$TEST_DBNAME-settings"
TESTS_DIR=${DJANGO_TESTS_DIR:-django_tests}

cd $TESTS_DIR/django/tests

EXIT_STATUS=0
for DJANGO_TEST_APP in $DJANGO_TEST_APPS
do
   python3 runtests.py $DJANGO_TEST_APP --verbosity=3 --noinput --settings tidb_settings || EXIT_STATUS=$?
   if [[ $EXIT_STATUS -ne 0 ]]; then
      exit $EXIT_STATUS
   fi
done
exit $EXIT_STATUS