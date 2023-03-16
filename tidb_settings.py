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

import os

hosts = os.getenv('TIDB_HOST')
if hosts is None:
    hosts = "127.0.0.1"

port = os.getenv('TIDB_PORT')
if port is None:
    port = 4000

DATABASES = {
    'default': {
        'ENGINE': 'django_tidb',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': 4000,
        'TEST': {
            'NAME': 'django_tests',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_general_ci',
        },
    },
    'other': {
        'ENGINE': 'django_tidb',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': hosts,
        'PORT': port,
        'TEST': {
            'NAME': 'django_tests2',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_general_ci',
        },
    },
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
USE_TZ = False
SECRET_KEY = 'django_tests_secret_key'
