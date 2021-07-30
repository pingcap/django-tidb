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
    def explain_query_prefix(self, format=None, **options):
        if format:
            supported_formats = self.connection.features.supported_explain_formats
            normalized_format = format.upper()
            if normalized_format not in supported_formats:
                msg = '%s is not a recognized format.' % normalized_format
                if supported_formats:
                    msg += ' Allowed formats: %s' % ', '.join(sorted(supported_formats))
                raise ValueError(msg)
        if options:
            raise ValueError('Unknown options: %s' % ', '.join(sorted(options.keys())))
        analyze = options.pop('analyze', False)
        prefix = self.explain_prefix
        if analyze and self.connection.features.supports_explain_analyze:
            prefix += ' ANALYZE'
        if format and not analyze:
            # Only TiDB supports the analyze option with formats but with "ROW".
            prefix += ' FORMAT=\"%s\"' % format
        return prefix

    def regex_lookup(self, lookup_type):
        # REGEXP BINARY doesn't work correctly in MySQL 8+ and REGEXP_LIKE
        # doesn't exist in MySQL 5.x or in MariaDB.
        if lookup_type == 'regex':
            return '%s REGEXP BINARY %s'
        return '%s REGEXP %s'

    def lookup_cast(self, lookup_type, internal_type=None):
        lookup = '%s'
        if internal_type == 'JSONField':
            lookup = 'JSON_UNQUOTE(%s)'
        return lookup
