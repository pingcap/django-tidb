# TiDB dialect for Django

![PyPI](https://img.shields.io/pypi/v/django-tidb)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-tidb)
![PyPI - Downloads](https://img.shields.io/pypi/dw/django-tidb)
[![.github/workflows/ci.yml](https://github.com/pingcap/django-tidb/actions/workflows/ci.yml/badge.svg)](https://github.com/pingcap/django-tidb/actions/workflows/ci.yml)

This adds compatibility for [TiDB](https://github.com/pingcap/tidb) to Django.

## Install

```
pip install django-tidb
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
- Django 3.2 and 4.1
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

Releases on PyPi before 3.0.0 are published from repository https://github.com/blacktear23/django_tidb. This repository is a new implementation and released under versions from 3.0.0. No backwards compatibility is ensured. The most significant points are:

- Only Django 3.2 and 4.0 are tested and supported.
- Engine name is `django_tidb` instead of `django_tidb.tidb`.

## Known issues

- TiDB before v6.6.0 does not support FOREIGN KEY constraints([#18209](https://github.com/pingcap/tidb/issues/18209)).
- TiDB before v6.2.0 does not support SAVEPOINT([#6840](https://github.com/pingcap/tidb/issues/6840)).

## Connect to TiDB Cloud Serverless

TiDB Serverless offers the TiDB database with full HTAP capabilities for you and your organization. It is a fully managed, auto-scaling deployment of TiDB that lets you start using your database immediately, develop and run your application without caring about the underlying nodes, and automatically scale based on your application's workload changes.

### 0. Signup to [TiDB Cloud](https://tidbcloud.com/signup?utm_source=github&utm_medium=django_tidb)

### 1. Create a [serverless cluster](https://tidbcloud.com/console/clusters/create-cluster?utm_source=github&utm_medium=django_tidb)

### 2. Obtain TiDB serverless [connection parameters](https://docs.pingcap.com/tidbcloud/connect-via-standard-connection-serverless#obtain-tidb-serverless-connection-parameters)

Example

```text
host: 'gateway01.us-east-1.prod.aws.tidbcloud.com',
port: 4000,
user: 'xxxxxx.root',
password: '<your_password>',
ssl_ca: /etc/ssl/cert.pem   # macos
```

### 3. Determain your root certificate based on your system

[Root certificate default path](https://docs.pingcap.com/tidbcloud/secure-connections-to-serverless-clusters#root-certificate-default-path)

### 4. Connect to Serverless cluster

Edit `DATABASES` in `settings.py` like below

```python
DATABASES = {
    'default': {
        'ENGINE': 'django_tidb',
        'HOST': host,
        'PORT': port,
        'USER': user,
        'PASSWORD': password,
        'NAME': db_name,
        'OPTIONS': {
            'ssl_mode': 'VERIFY_IDENTITY',
            'ssl': {
                'ca': '/etc/ssl/cert.pem'
            }
        }

    }
}
```

You got it, enjoy!
