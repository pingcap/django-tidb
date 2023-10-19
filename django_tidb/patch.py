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

from django.db.models.functions import Chr
from django.db.models import options
from django.db.migrations import state


def char(self, compiler, connection, **extra_context):
    # TiDB doesn't support utf16
    return self.as_sql(
        compiler,
        connection,
        function="CHAR",
        template="%(function)s(%(expressions)s USING utf8mb4)",
        **extra_context,
    )


def patch_model_functions():
    Chr.as_mysql = char


def patch_model_options():
    # Patch `tidb_auto_id_cache` to options.DEFAULT_NAMES,
    # so that user can define it in model's Meta class.
    options.DEFAULT_NAMES += ("tidb_auto_id_cache",)
    # Because Django named import DEFAULT_NAMES in migrations,
    # so we need to patch it again here.
    # Django will record `tidb_auto_id_cache` in migration files,
    # and then restore it when applying migrations.
    state.DEFAULT_NAMES += ("tidb_auto_id_cache",)


def monkey_patch():
    patch_model_functions()
    patch_model_options()
