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

from django.db.backends.mysql.operations import (
    DatabaseOperations as MysqlDatabaseOperations,
)


class DatabaseOperations(MysqlDatabaseOperations):
    integer_field_ranges = {
        **MysqlDatabaseOperations.integer_field_ranges,
        "BigAutoRandomField": (-9223372036854775808, 9223372036854775807),
    }

    def explain_query_prefix(self, format=None, **options):
        # Alias TiDB's "ROW" format to "TEXT" for consistency with other backends.
        if format and format.upper() == "TEXT":
            format = "ROW"
        elif not format:
            format = "ROW"

        # Check if the format is supported by TiDB.
        supported_formats = self.connection.features.supported_explain_formats
        normalized_format = format.upper()
        if normalized_format not in supported_formats:
            msg = "%s is not a recognized format." % normalized_format
            if supported_formats:
                msg += " Allowed formats: %s" % ", ".join(sorted(supported_formats))
            else:
                msg += f" {self.connection.display_name} does not support any formats."
            raise ValueError(msg)

        analyze = options.pop("analyze", False)
        if options:
            raise ValueError("Unknown options: %s" % ", ".join(sorted(options.keys())))

        prefix = self.explain_prefix
        if analyze:
            prefix += " ANALYZE"
        prefix += ' FORMAT="%s"' % format
        return prefix

    def regex_lookup(self, lookup_type):
        # REGEXP BINARY doesn't work correctly in MySQL 8+ and REGEXP_LIKE
        # doesn't exist in MySQL 5.x or in MariaDB.
        if lookup_type == "regex":
            return "%s REGEXP BINARY %s"
        return "%s REGEXP %s"
