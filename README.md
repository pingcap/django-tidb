# TiDB dialect for Django

[![.github/workflows/ci.yml](https://github.com/pingcap/django-tidb/actions/workflows/ci.yml/badge.svg)](https://github.com/pingcap/django-tidb/actions/workflows/ci.yml)

This adds compatibility for [TiDB](https://github.com/pingcap/tidb) to Django.

## Install

```
pip install git+https://github.com/pingcap/django-tidb.git@main
```

## Usage

Set `'ENGINE': 'django_tidb'` in your settings to this:

```
DATABASES = {
    'default': {
        'ENGINE': 'django_tidb',
        'NAME': 'django',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': 4000,
    },
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
USE_TZ = False
SECRET_KEY = 'django_tests_secret_key'
```

## Supported versions

- TiDB 4.0 and newer
- Django 3.x and 4.0
- Python 3.6 and newer(must match Django's Python version requirement)

## Test

create your virtualenv with:

```
$ virtualenv venv
$ source venv/bin/activate
```

you can use the command ```deactivate``` to exit from the virtual environment.

run all integration tests.

```
$ DJANGO_VERSION=3.2.12 python run_testing_worker.py
```

## Migrate from previous versions

Releases on PyPi before 3.0.0 are published from repository https://github.com/blacktear23/django_tidb. This repository is new implementation and released under versions from 3.0.0. No backwards compatibility is ensured. The most significant points are:

- Only Django 3.x and 4.0 are tested and supported.
- Engine name is `django_tidb` instead of `django_tidb.tidb`.

## Known issues

- TiDB does not support FOREIGN KEY constraints([#18209](https://github.com/pingcap/tidb/issues/18209)).
- TiDB does not support SAVEPOINT([#6840](https://github.com/pingcap/tidb/issues/6840)).
