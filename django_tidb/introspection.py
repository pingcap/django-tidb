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
from django.db.models import Index
from django.utils.datastructures import OrderedSet

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

    def get_constraints(self, cursor, table_name):
        """
        Retrieve any constraints or keys (unique, pk, fk, check, index) across
        one or more columns.
        """
        constraints = {}
        # Get the actual constraint names and columns
        name_query = """
            SELECT kc.`constraint_name`, kc.`column_name`,
                kc.`referenced_table_name`, kc.`referenced_column_name`,
                c.`constraint_type`
            FROM
                information_schema.key_column_usage AS kc,
                information_schema.table_constraints AS c
            WHERE
                kc.table_schema = DATABASE() AND
                c.table_schema = kc.table_schema AND
                c.constraint_name = kc.constraint_name AND
                c.constraint_type != 'CHECK' AND
                kc.table_name = %s
            ORDER BY kc.`ordinal_position`
        """
        cursor.execute(name_query, [table_name])
        for constraint, column, ref_table, ref_column, kind in cursor.fetchall():
            if constraint not in constraints:
                constraints[constraint] = {
                    "columns": OrderedSet(),
                    "primary_key": kind == "PRIMARY KEY",
                    "unique": kind in {"PRIMARY KEY", "UNIQUE"},
                    "index": False,
                    "check": False,
                    "foreign_key": (ref_table, ref_column) if ref_column else None,
                }
                if self.connection.features.supports_index_column_ordering:
                    constraints[constraint]["orders"] = []
            constraints[constraint]["columns"].add(column)
        # Add check constraints.
        if self.connection.features.can_introspect_check_constraints:
            unnamed_constraints_index = 0
            columns = {
                info.name for info in self.get_table_description(cursor, table_name)
            }
            type_query = """
                    SELECT cc.constraint_name, cc.check_clause
                    FROM
                        information_schema.check_constraints AS cc,
                        information_schema.table_constraints AS tc
                    WHERE
                        cc.constraint_schema = DATABASE() AND
                        tc.table_schema = cc.constraint_schema AND
                        cc.constraint_name = tc.constraint_name AND
                        tc.constraint_type = 'CHECK' AND
                        tc.table_name = %s
                """
            cursor.execute(type_query, [table_name])
            for constraint, check_clause in cursor.fetchall():
                constraint_columns = self._parse_constraint_columns(
                    check_clause, columns
                )
                # Ensure uniqueness of unnamed constraints. Unnamed unique
                # and check columns constraints have the same name as
                # a column.
                if set(constraint_columns) == {constraint}:
                    unnamed_constraints_index += 1
                    constraint = "__unnamed_constraint_%s__" % unnamed_constraints_index
                constraints[constraint] = {
                    "columns": constraint_columns,
                    "primary_key": False,
                    "unique": False,
                    "index": False,
                    "check": True,
                    "foreign_key": None,
                }
        # Now add in the indexes
        cursor.execute(
            "SHOW INDEX FROM %s" % self.connection.ops.quote_name(table_name)
        )
        for table, non_unique, index, colseq, column, order, type_ in [
            x[:6] + (x[10],) for x in cursor.fetchall()
        ]:
            if index not in constraints:
                constraints[index] = {
                    "columns": OrderedSet(),
                    "primary_key": False,
                    "unique": not non_unique,
                    "check": False,
                    "foreign_key": None,
                }
                if self.connection.features.supports_index_column_ordering:
                    constraints[index]["orders"] = []
            constraints[index]["index"] = True
            constraints[index]["type"] = (
                Index.suffix if type_ == "BTREE" else type_.lower()
            )
            constraints[index]["columns"].add(column)
            if self.connection.features.supports_index_column_ordering:
                constraints[index]["orders"].append("DESC" if order == "D" else "ASC")
        # Convert the sorted sets to lists
        for constraint in constraints.values():
            constraint["columns"] = list(constraint["columns"])
        return constraints
