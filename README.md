# TiDB dialect for Django

![PyPI](https://img.shields.io/pypi/v/django-tidb)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-tidb)
![PyPI - Downloads](https://img.shields.io/pypi/dw/django-tidb)
[![.github/workflows/ci.yml](https://github.com/pingcap/django-tidb/actions/workflows/ci.yml/badge.svg)](https://github.com/pingcap/django-tidb/actions/workflows/ci.yml)

This adds compatibility for [TiDB](https://github.com/pingcap/tidb) to Django.

## Installation Guide

### Prerequisites

Before installing django-tidb, ensure you have a MySQL driver installed. You can choose either `mysqlclient`(recommended) or `pymysql`(at your own risk).

#### Install mysqlclient (Recommended)

Please refer to the [mysqlclient official guide](https://github.com/PyMySQL/mysqlclient#install)

#### Install pymysql (At your own risk)

> django-tidb has not been tested with pymysql

```bash
pip install pymysql
```

Then add the following code at the beginning of your Django's `settings.py`:

```python
import pymysql

pymysql.install_as_MySQLdb()
```

### Installing django-tidb

To install django-tidb, you need to select the version that corresponds with your Django version. Please refer to the table below for guidance:

> The minor release number of Django doesn't correspond to the minor release number of django-tidb. Use the latest minor release of each.

|django|django-tidb|install command|
|:----:|:---------:|:-------------:|
|v4.2.x|v4.2.x|`pip install 'django-tidb>=4.2.0,<4.3.0'`|
|v4.1.x|v4.1.x|`pip install 'django-tidb>=4.1.0,<4.2.0'`|
|v3.2.x|v3.2.x|`pip install 'django-tidb>=3.2.0,<3.3.0'`|

## Usage

Set `'ENGINE': 'django_tidb'` in your settings to this:

```python
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
- Django 3.2, 4.1 and 4.2
- Python 3.6 and newer(must match Django's Python version requirement)

## Test

create your virtualenv with:

```bash
$ virtualenv venv
$ source venv/bin/activate
```

you can use the command ```deactivate``` to exit from the virtual environment.

run all integration tests.

```bash
$ DJANGO_VERSION=3.2.12 python run_testing_worker.py
```

## Migrate from previous versions

Releases on PyPi before 3.0.0 are published from repository https://github.com/blacktear23/django_tidb. This repository is a new implementation and released under versions from 3.0.0. No backwards compatibility is ensured. The most significant points are:

- Only Django 3.2 and 4.0 are tested and supported.
- Engine name is `django_tidb` instead of `django_tidb.tidb`.

## Known issues

- TiDB before v6.6.0 does not support FOREIGN KEY constraints([#18209](https://github.com/pingcap/tidb/issues/18209)).
- TiDB before v6.2.0 does not support SAVEPOINT([#6840](https://github.com/pingcap/tidb/issues/6840)).
