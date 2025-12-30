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

from collections import namedtuple

from django.db.backends.base.introspection import FieldInfo as BaseFieldInfo
from django.db.backends.mysql.introspection import (
    DatabaseIntrospection as MysqlDatabaseIntrospection,
)

FieldInfo = namedtuple(
    "FieldInfo",
    BaseFieldInfo._fields
    + ("extra", "is_unsigned", "has_json_constraint", "comment", "data_type"),
)
InfoLine = namedtuple(
    "InfoLine",
    "col_name data_type max_len num_prec num_scale extra column_default "
    "collation is_unsigned comment",
)


class DatabaseIntrospection(MysqlDatabaseIntrospection):
    def get_table_description(self, cursor, table_name):
        """
        Return a description of the table with the DB-API cursor.description
        interface."
        """
        json_constraints = {}
        if self.connection.features.can_introspect_json_field:
            # JSON data type is an alias for LONGTEXT in MariaDB, select
            # JSON_VALID() constraints to introspect JSONField.
            cursor.execute(
                """
                SELECT c.constraint_name AS column_name
                FROM information_schema.check_constraints AS c
                WHERE
                    c.table_name = %s AND
                    LOWER(c.check_clause) = 'json_valid(`' + LOWER(c.constraint_name) + '`)' AND
                    c.constraint_schema = DATABASE()
            """,
                [table_name],
            )
            json_constraints = {row[0] for row in cursor.fetchall()}
        # A default collation for the given table.
        cursor.execute(
            """
            SELECT  table_collation
            FROM    information_schema.tables
            WHERE   table_schema = DATABASE()
            AND     table_name = %s
        """,
            [table_name],
        )
        row = cursor.fetchone()
        default_column_collation = row[0] if row else ""
        # information_schema database gives more accurate results for some figures:
        # - varchar length returned by cursor.description is an internal length,
        #   not visible length (#5725)
        # - precision and scale (for decimal fields) (#5014)
        # - auto_increment is not available in cursor.description
        cursor.execute(
            """
            SELECT
                column_name, data_type, character_maximum_length,
                numeric_precision, numeric_scale, extra, column_default,
                CASE
                    WHEN collation_name = %s THEN NULL
                    ELSE collation_name
                END AS collation_name,
                CASE
                    WHEN column_type LIKE '%% unsigned' THEN 1
                    ELSE 0
                END AS is_unsigned,
                column_comment
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = DATABASE()
        """,
            [default_column_collation, table_name],
        )
        field_info = {line[0]: InfoLine(*line) for line in cursor.fetchall()}

        cursor.execute(
            "SELECT * FROM %s LIMIT 1" % self.connection.ops.quote_name(table_name)
        )

        def to_int(i):
            return int(i) if i is not None else i

        fields = []
        for line in cursor.description:
            info = field_info[line[0]]
            fields.append(
                FieldInfo(
                    *line[:2],
                    to_int(info.max_len) or line[2],
                    to_int(info.max_len) or line[3],
                    to_int(info.num_prec) or line[4],
                    to_int(info.num_scale) or line[5],
                    line[6],
                    info.column_default,
                    info.collation,
                    info.extra,
                    info.is_unsigned,
                    line[0] in json_constraints,
                    info.comment,
                    info.data_type,
                )
            )
        return fields
