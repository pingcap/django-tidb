# Copyright 2021 PingCAP, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# See the License for the specific language governing permissions and
# limitations under the License.

import django
from django.core.exceptions import ImproperlyConfigured
from django.utils.version import get_version_tuple


def check_django_compatability():
    """
    Verify that this version of django-cockroachdb is compatible with the
    installed version of Django. For example, any django-tidb 2.2.x is
    compatible with Django 2.2.y.
    """
    from . import __version__
    if django.VERSION[:2] != get_version_tuple(__version__)[:2]:
        raise ImproperlyConfigured(
            'You must use the latest version of django-tidb {A}.{B}.x '
            'with Django {A}.{B}.y (found django-tidb {C}).'.format(
                A=django.VERSION[0],
                B=django.VERSION[1],
                C=__version__,
            )
        )
