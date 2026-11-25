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

> The patch release number of Django doesn't correspond to the patch release number of django-tidb. For example, django-tidb 6.0.x works with every Django 6.0.x. Use the latest patch release of each.

|django|django-tidb|install command|
|:----:|:---------:|:-------------:|
|v6.0.x|v6.0.x|`pip install 'django-tidb~=6.0.0'`|
|v5.2.x|v5.2.x|`pip install 'django-tidb~=5.2.0'`|
|v5.1.x|v5.1.x|`pip install 'django-tidb~=5.1.0'`|
|v5.0.x|v5.0.x|`pip install 'django-tidb~=5.0.0'`|
|v4.2.x|v4.2.x|`pip install 'django-tidb~=4.2.0'`|
|v4.1.x|v4.1.x|`pip install 'django-tidb~=4.1.0'`|
|v3.2.x|v3.2.x|`pip install 'django-tidb~=3.2.0'`|

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
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

- [AUTO_RANDOM](#using-auto_random)
- [AUTO_ID_CACHE](#using-auto_id_cache)
- [Vector (Beta)](#vector-beta)

### Using `AUTO_RANDOM`

[`AUTO_RANDOM`](https://docs.pingcap.com/tidb/stable/auto-random) is a feature in TiDB that generates unique IDs for a table automatically. It is similar to `AUTO_INCREMENT`, but it can avoid write hotspot in a single storage node caused by TiDB assigning consecutive IDs. It also has some restrictions, please refer to the [documentation](https://docs.pingcap.com/tidb/stable/auto-random#restrictions).

To use `AUTO_RANDOM` in Django, you can do it in either of the following two ways:

1. Declare globally in `settings.py` as shown below, it will affect all models:

    ```python
    DEFAULT_AUTO_FIELD = 'django_tidb.fields.BigAutoRandomField'
    ```

2. Manually declare it in the model as shown below:

    ```python
    from django_tidb.fields import BigAutoRandomField

    class MyModel(models.Model):
        id = BigAutoRandomField(primary_key=True)
        title = models.CharField(max_length=200)
    ```

`BigAutoRandomField` is a subclass of `BigAutoField`, it can only be used for primary key and its behavior can be controlled by setting the parameters `shard_bits` and `range`. For detailed information, please refer to the [documentation](https://docs.pingcap.com/tidb/stable/auto-random#basic-concepts).

Migrate from `AUTO_INCREMENT` to `AUTO_RANDOM`:

1. Check if the original column is `BigAutoField(bigint)`, if not, migrate it to `BigAutoField(bigint)` first.
2. In the database configuration (`settings.py`), define [`SET @@tidb_allow_remove_auto_inc = ON`](https://docs.pingcap.com/tidb/stable/system-variables#tidb_allow_remove_auto_inc-new-in-v2118-and-v304) in the `init_command`. You can remove it after completing the migration.

    ```python
    # settings.py
    DATABASES = {
        'default': {
            'ENGINE': 'django_tidb',
            ...
            'OPTIONS': {
                'init_command': 'SET @@tidb_allow_remove_auto_inc = ON',
            }

        }
    }
    ```

3. Finally, migrate it to `BigAutoRandomField(bigint)`.

> **Note**
>
> `AUTO_RANDOM` is supported after TiDB v3.1.0, and only support define with `range` after v6.3.0, so `range` will be ignored if TiDB version is lower than v6.3.0

### Using `AUTO_ID_CACHE`

[`AUTO_ID_CACHE`](https://docs.pingcap.com/tidb/stable/auto-increment#auto_id_cache) allows users to set the cache size for allocating auto-increment IDs. TiDB guarantees that `AUTO_INCREMENT` values are monotonic (always increasing) on a per-server basis, but the value may appear to jump dramatically if an `INSERT` is performed against another TiDB server, because each server has its own cache, whose size is controlled by `AUTO_ID_CACHE`. TiDB v6.4.0 introduced a centralized auto-increment ID allocating service: setting `AUTO_ID_CACHE` to `1` when creating a table enables [*MySQL compatibility mode*](https://docs.pingcap.com/tidb/stable/auto-increment#mysql-compatibility-mode) without losing performance.

To use `AUTO_ID_CACHE` in Django, you can specify `tidb_auto_id_cache` in the model's `Meta` class as shown below when creating a new table:

```python
class MyModel(models.Model):
    title = models.CharField(max_length=200)

    class Meta:
        tidb_auto_id_cache = 1
```

But there are some limitations:

- `tidb_auto_id_cache` can only affect the table creation, after that it will be ignored even if you change it.
- `tidb_auto_id_cache` only affects the `AUTO_INCREMENT` column.

### Vector (Beta)

TiDB supports the vector data type on TiDB Cloud, and on TiDB Self-Managed from v8.4.0 (experimental). See [Vector Search Overview](https://docs.pingcap.com/tidb/stable/vector-search-overview/).

`VectorField` is still in beta, and the API may change in the future.

To use `VectorField` in Django, you need to install `django-tidb` with `vector` extra:

```bash
pip install 'django-tidb[vector]'
```

Then you can use `VectorField` in your model:

```python
from django.db import models
from django_tidb.fields.vector import VectorField

class Test(models.Model):
    embedding = VectorField(dimensions=3)
```

You can also add an HNSW vector index when creating the table. For more information, see [Vector Search Index](https://docs.pingcap.com/tidb/stable/vector-search-index/).
A vector index is built on TiFlash, so the cluster needs a TiFlash node. django-tidb sets a TiFlash replica for the table (`ALTER TABLE ... SET TIFLASH REPLICA 1`) before it creates the index.

```python
from django_tidb.fields.vector import L2Distance, VectorField, VectorIndex

class Test(models.Model):
    embedding = VectorField(dimensions=3)
    class Meta:
        indexes = [
            VectorIndex(L2Distance("embedding"), name='idx_l2'),
        ]
```

#### Create a record

```python
Test.objects.create(embedding=[1, 2, 3])
```

#### Get instances with vector field

TiDB supports the following vector distance functions:

- `L1Distance`
- `L2Distance`
- `CosineDistance`
- `NegativeInnerProduct`

They can be imported from `django_tidb.fields.vector`. See [Vector Functions and Operators](https://docs.pingcap.com/tidb/stable/vector-search-functions-and-operators/).

Get instances with vector field and calculate distance to a given vector:

```python
from django_tidb.fields.vector import CosineDistance

Test.objects.annotate(distance=CosineDistance('embedding', [3, 1, 2]))
```

Get instances with vector field and calculate distance to a given vector, and filter by distance:

```python
Test.objects.alias(distance=CosineDistance('embedding', [3, 1, 2])).filter(distance__lt=5)
```

## Supported versions

- TiDB 6.2 and newer. TiDB before v6.2.0 does not support `SAVEPOINT`, which
  Django 4.2 and newer rely on. CI tests the
  [LTS releases](https://www.pingcap.com/tidb-release-support-policy/) from v6.5.
- Django 6.0. For other Django versions, use the matching django-tidb release
  (see [Installing django-tidb](#installing-django-tidb)).
- Python 3.12 and newer, as required by Django 6.0.

## Test

create your virtualenv with:

```bash
$ python -m venv .venv
$ source .venv/bin/activate
```

you can use the command `deactivate` to exit from the virtual environment.

run all integration tests.

```bash
$ DJANGO_VERSION=6.0 python run_testing_worker.py
```

## Migrate from previous versions

Releases on PyPI before 3.0.0 are published from repository https://github.com/blacktear23/django_tidb. This repository is a new implementation and released under versions from 3.0.0. No backwards compatibility is ensured. The most significant points are:

- Engine name is `django_tidb` instead of `django_tidb.tidb`.

## Known issues

- TiDB before v6.6.0 does not support FOREIGN KEY constraints([#18209](https://github.com/pingcap/tidb/issues/18209)).
- TiDB before v6.2.0 does not support SAVEPOINT([#6840](https://github.com/pingcap/tidb/issues/6840)).
- TiDB has limited support for default value expressions, please refer to the [documentation](https://docs.pingcap.com/tidb/dev/data-type-default-values#specify-expressions-as-default-values).
