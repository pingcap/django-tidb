# TiDB dialect for Django

This adds compatibility for [TiDB](https://github.com/pingcap/tidb) to Django.

## Installation

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

- TiDB 5.x (tested with 5.1.x)
- Django 3.x (tested with 3.2.x)
- mysqlclient 2.0.3
- Python 3.6 and newer (tested with Python 3.8)

## Testing

create your virtualenv with:

```
$ virtualenv venv
$ source venv/bin/activate
```

you can use the command ```deactivate``` to exit from the virtual environment.

run all integration tests.

```
$ python run_testing_worker.py
```

## Known issues

- TiDB does not support FOREIGN KEY constraints([#18209](https://github.com/pingcap/tidb/issues/18209)).
- TiDB does not support SAVEPOINT([#6840](https://github.com/pingcap/tidb/issues/6840)).
