# TiDB dialect for Django

This adds compatibility for [TiDB](https://github.com/pingcap/tidb) to Django.

## Usage

Set `'ENGINE': 'django_tidb'` in your settings.

## Supported versions

- TiDB 5.x (tested with 5.1.x)
- Django 3.x (tested with 3.2.x)
- mysqlclient 2.0.3
- Python 3.6 an newer (tested with Python 3.8)

## Known issues

- TiDB does not support foreign keys.
