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

from django.db.backends.mysql.schema import (
    DatabaseSchemaEditor as MysqlDatabaseSchemaEditor,
)


class DatabaseSchemaEditor(MysqlDatabaseSchemaEditor):
    # Unsupported add column and foreign key in single statement
    # https://github.com/pingcap/tidb/issues/45474
    sql_create_column_inline_fk = None

    @property
    def sql_delete_check(self):
        return "ALTER TABLE %(table)s DROP CHECK %(name)s"

    @property
    def sql_rename_column(self):
        return "ALTER TABLE %(table)s CHANGE %(old_column)s %(new_column)s %(type)s"

    def skip_default_on_alter(self, field):
        if self._is_limited_data_type(field):
            # TiDB doesn't support defaults for BLOB/TEXT/JSON in the
            # ALTER COLUMN statement.
            return True
        return False

    @property
    def _supports_limited_data_type_defaults(self):
        return False

    def _field_should_be_indexed(self, model, field):
        return False
