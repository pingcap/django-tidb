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

import operator

from django.db.backends.mysql.features import (
    DatabaseFeatures as MysqlDatabaseFeatures,
)
from django.utils.functional import cached_property


class DatabaseFeatures(MysqlDatabaseFeatures):
    has_select_for_update = True
    has_native_uuid_field = False
    atomic_transactions = False
    supports_atomic_references_rename = False
    can_clone_databases = False
    can_rollback_ddl = False
    # Unsupported add column and foreign key in single statement
    # https://github.com/pingcap/tidb/issues/45474
    can_create_inline_fk = False
    order_by_nulls_first = True
    create_test_procedure_without_params_sql = None
    create_test_procedure_with_int_param_sql = None
    test_collations = {
        "ci": "utf8mb4_general_ci",
        "non_default": "utf8mb4_bin",
        "virtual": "utf8mb4_general_ci",
    }

    minimum_database_version = (5,)

    @cached_property
    def supports_foreign_keys(self):
        if self.connection.tidb_version >= (6, 6, 0):
            return True
        return False

    @cached_property
    def indexes_foreign_keys(self):
        if self.connection.tidb_version >= (6, 6, 0):
            return True
        return False

    @cached_property
    def supports_transactions(self):
        # https://code.djangoproject.com/ticket/28263
        if self.connection.tidb_version >= (6, 2, 0):
            return True
        return False

    @cached_property
    def uses_savepoints(self):
        if self.connection.tidb_version >= (6, 2, 0):
            return True
        return False

    @cached_property
    def can_release_savepoints(self):
        if self.connection.tidb_version >= (6, 2, 0):
            return True
        return False

    @cached_property
    def django_test_skips(self):
        skips = {
            "This doesn't work on MySQL.": {
                "db_functions.comparison.test_greatest.GreatestTests.test_coalesce_workaround",
                "db_functions.comparison.test_least.LeastTests.test_coalesce_workaround",
                # UPDATE ... ORDER BY syntax on MySQL/MariaDB does not support ordering by related fields
                "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation_desc",
            },
            "MySQL doesn't support functional indexes on a function that "
            "returns JSON": {
                "schema.tests.SchemaTests.test_func_index_json_key_transform",
            },
            "MySQL supports multiplying and dividing DurationFields by a "
            "scalar value but it's not implemented (#25287).": {
                "expressions.tests.FTimeDeltaTests.test_durationfield_multiply_divide",
            },
            "tidb": {
                # Unknown column 'annotations_publisher.id' in 'where clause'
                # https://github.com/pingcap/tidb/issues/45181
                "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_filter_with_subquery",
                # Designed for MySQL only
                "backends.mysql.test_features.TestFeatures.test_supports_transactions",
                "backends.mysql.tests.Tests.test_check_database_version_supported",
                "backends.mysql.test_introspection.StorageEngineTests.test_get_storage_engine",
                "check_framework.test_database.DatabaseCheckTests.test_mysql_strict_mode",
                # Unsupported add column and foreign key in single statement
                "indexes.tests.SchemaIndexesMySQLTests.test_no_index_for_foreignkey",
                # TiDB does not support `JSON` format for `EXPLAIN ANALYZE`
                "queries.test_explain.ExplainTests.test_mysql_analyze",
                "queries.test_explain.ExplainTests.test_mysql_text_to_traditional",
                # TiDB cannot guarantee to always rollback the main thread txn when deadlock occurs
                "transactions.tests.AtomicMySQLTests.test_implicit_savepoint_rollback",
                "filtered_relation.tests.FilteredRelationTests.test_union",
                # [planner:3065]Expression #1 of ORDER BY clause is not in SELECT list, references column '' which is
                # not in SELECT list; this is incompatible with
                "ordering.tests.OrderingTests.test_orders_nulls_first_on_filtered_subquery",
                # Unsupported modify column: this column has primary key flag
                "schema.tests.SchemaTests.test_alter_auto_field_to_char_field",
                # Unsupported modify column: can't remove auto_increment without @@tidb_allow_remove_auto_inc enabled
                "schema.tests.SchemaTests.test_alter_auto_field_to_integer_field",
                # Found wrong number (0) of check constraints for schema_author.height
                "schema.tests.SchemaTests.test_alter_field_default_dropped",
                # Unsupported modify column: can't set auto_increment
                "schema.tests.SchemaTests.test_alter_int_pk_to_autofield_pk",
                "schema.tests.SchemaTests.test_alter_int_pk_to_bigautofield_pk",
                # Unsupported drop primary key when the table's pkIsHandle is true
                "schema.tests.SchemaTests.test_alter_int_pk_to_int_unique",
                # Unsupported drop integer primary key
                "schema.tests.SchemaTests.test_alter_not_unique_field_to_primary_key",
                # Unsupported modify column: can't set auto_increment
                "schema.tests.SchemaTests.test_alter_smallint_pk_to_smallautofield_pk",
                # Unsupported modify column: this column has primary key flag
                "schema.tests.SchemaTests.test_char_field_pk_to_auto_field",
                # Unsupported modify charset from utf8mb4 to utf8
                "schema.tests.SchemaTests.test_ci_cs_db_collation",
                # Unsupported drop integer primary key
                "schema.tests.SchemaTests.test_primary_key",
                "schema.tests.SchemaTests.test_add_auto_field",
                "schema.tests.SchemaTests.test_alter_autofield_pk_to_smallautofield_pk",
                "schema.tests.SchemaTests.test_alter_primary_key_db_collation",
                "schema.tests.SchemaTests.test_alter_primary_key_the_same_name",
                "schema.tests.SchemaTests.test_autofield_to_o2o",
                "update.tests.AdvancedTests.test_update_ordered_by_inline_m2m_annotation",
                "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation",
                # IntegrityError not raised
                "constraints.tests.CheckConstraintTests.test_database_constraint",
                "constraints.tests.CheckConstraintTests.test_database_constraint_unicode",
                # Result of function ROUND(x, d) is different from MySQL
                # https://github.com/pingcap/tidb/issues/26993
                "db_functions.math.test_round.RoundTests.test_integer_with_negative_precision",
                "db_functions.text.test_chr.ChrTests.test_transform",
                "db_functions.text.test_chr.ChrTests.test_non_ascii",
                "db_functions.text.test_chr.ChrTests.test_basic",
                "db_functions.comparison.test_collate.CollateTests.test_collate_filter_ci",
                # Unsupported modifying collation of column from 'utf8mb4_general_ci' to 'utf8mb4_bin'
                # when index is defined on it.
                "migrations.test_operations.OperationTests.test_alter_field_pk_fk_db_collation",
                "migrations.test_executor.ExecutorTests.test_alter_id_type_with_fk",
                "migrations.test_operations.OperationTests.test_alter_field_pk",
                "migrations.test_operations.OperationTests.test_alter_field_reloads_state_on_fk_target_changes",
                "migrations.test_operations.OperationTests.test_rename_field_reloads_state_on_fk_target_changes",
                # Unsupported modifying the Reorg-Data types on the primary key
                "migrations.test_operations.OperationTests.test_alter_field_pk_fk",
                "migrations.test_operations.OperationTests.test_alter_field_pk_fk_char_to_int",
                "migrations.test_operations.OperationTests.test_add_constraint",
                "migrations.test_operations.OperationTests.test_add_constraint_combinable",
                "migrations.test_operations.OperationTests.test_add_constraint_percent_escaping",
                "migrations.test_operations.OperationTests.test_add_or_constraint",
                "migrations.test_operations.OperationTests.test_create_model_with_constraint",
                "migrations.test_operations.OperationTests.test_remove_constraint",
                "migrations.test_operations.OperationTests.test_alter_field_pk_mti_and_fk_to_base",
                "migrations.test_operations.OperationTests.test_alter_field_pk_mti_fk",
                "migrations.test_operations.OperationTests.test_create_model_with_boolean_expression_in_check_constraint",
                # Unsupported adding a stored generated column through ALTER TABLE
                "migrations.test_operations.OperationTests.test_add_field_after_generated_field",
                "migrations.test_operations.OperationTests.test_add_generated_field_stored",
                "migrations.test_operations.OperationTests.test_invalid_generated_field_changes_stored",
                "migrations.test_operations.OperationTests.test_invalid_generated_field_persistency_change",
                "migrations.test_operations.OperationTests.test_remove_generated_field_stored",
                "schema.tests.SchemaTests.test_add_generated_field_contains",
                # Failed to modify column's default value when has expression index
                # https://github.com/pingcap/tidb/issues/52355
                "migrations.test_operations.OperationTests.test_alter_field_with_func_index",
                # TiDB has limited support for default value expressions
                # https://docs.pingcap.com/tidb/dev/data-type-default-values#specify-expressions-as-default-values
                "migrations.test_operations.OperationTests.test_add_field_database_default_function",
                "schema.tests.SchemaTests.test_add_text_field_with_db_default",
                "schema.tests.SchemaTests.test_db_default_equivalent_sql_noop",
                "schema.tests.SchemaTests.test_db_default_output_field_resolving",
                # about Pessimistic/Optimistic Transaction Model
                "select_for_update.tests.SelectForUpdateTests.test_raw_lock_not_available",
                # Wrong referenced_table_schema in information_schema.key_column_usage
                # https://github.com/pingcap/tidb/issues/52350
                "backends.mysql.test_introspection.TestCrossDatabaseRelations.test_omit_cross_database_relations",
            },
        }
        if self.connection.tidb_version < (5,):
            skips.update(
                {
                    "tidb4": {
                        # Unsupported modify column
                        "schema.tests.SchemaTests.test_rename",
                        "schema.tests.SchemaTests.test_m2m_rename_field_in_target_model",
                        "schema.tests.SchemaTests.test_alter_textual_field_keep_null_status",
                        "schema.tests.SchemaTests.test_alter_text_field_to_time_field",
                        "schema.tests.SchemaTests.test_alter_text_field_to_datetime_field",
                        "schema.tests.SchemaTests.test_alter_text_field_to_date_field",
                        "schema.tests.SchemaTests.test_alter_field_type_and_db_collation",
                        # wrong result
                        "expressions_window.tests.WindowFunctionTests.test_subquery_row_range_rank",
                        "migrations.test_operations.OperationTests.test_alter_fk_non_fk",
                        "migrations.test_operations.OperationTests"
                        ".test_alter_field_reloads_state_on_fk_with_to_field_target_changes",
                        "model_fields.test_integerfield.PositiveIntegerFieldTests.test_negative_values",
                    }
                }
            )
        if self.connection.tidb_version < (6, 3):
            skips.update(
                {
                    "auto_random": {
                        "tidb.test_tidb_auto_random.TiDBAutoRandomMigrateTests"
                        ".test_create_table_explicit_auto_random_field_with_shard_bits_and_range",
                        "tidb.test_tidb_auto_random.TiDBAutoRandomMigrateTests"
                        ".test_create_table_explicit_auto_random_field_with_range",
                    }
                }
            )
        if self.connection.tidb_version < (6, 6):
            skips.update(
                {
                    "tidb653": {
                        "fixtures_regress.tests.TestFixtures.test_loaddata_raises_error_when_fixture_has_invalid_foreign_key",
                        "migrations.test_operations.OperationTests.test_autofield__bigautofield_foreignfield_growth",
                        "migrations.test_operations.OperationTests.test_smallfield_autofield_foreignfield_growth",
                        "migrations.test_operations.OperationTests.test_smallfield_bigautofield_foreignfield_growth",
                        "migrations.test_commands.MigrateTests.test_migrate_syncdb_app_label",
                        "migrations.test_commands.MigrateTests.test_migrate_syncdb_deferred_sql_executed_with_schemaeditor",
                        "schema.tests.SchemaTests.test_rename_column_renames_deferred_sql_references",
                        "schema.tests.SchemaTests.test_rename_table_renames_deferred_sql_references",
                    }
                }
            )
        if "ONLY_FULL_GROUP_BY" in self.connection.sql_mode:
            skips.update(
                {
                    "GROUP BY cannot contain nonaggregated column when "
                    "ONLY_FULL_GROUP_BY mode is enabled on TiDB.": {
                        "aggregation.tests.AggregateTestCase.test_group_by_nested_expression_with_params",
                    },
                }
            )
        if not self.supports_foreign_keys:
            skips.update(
                {
                    # Django does not check if the database supports foreign keys.
                    "django42_db_unsupport_foreign_keys": {
                        "inspectdb.tests.InspectDBTestCase.test_same_relations",
                    },
                }
            )
        return skips

    @cached_property
    def update_can_self_select(self):
        return True

    @cached_property
    def can_introspect_foreign_keys(self):
        if self.connection.tidb_version >= (6, 6, 0):
            return True
        return False

    @cached_property
    def can_return_columns_from_insert(self):
        return False

    can_return_rows_from_bulk_insert = property(
        operator.attrgetter("can_return_columns_from_insert")
    )

    @cached_property
    def has_zoneinfo_database(self):
        return self.connection.tidb_server_data["has_zoneinfo_database"]

    @cached_property
    def is_sql_auto_is_null_enabled(self):
        return self.connection.tidb_server_data["sql_auto_is_null"]

    @cached_property
    def supports_over_clause(self):
        return True

    supports_frame_range_fixed_distance = property(
        operator.attrgetter("supports_over_clause")
    )

    @cached_property
    def supports_column_check_constraints(self):
        return True

    @cached_property
    def supports_expression_defaults(self):
        # TiDB has limited support for default value expressions
        # https://docs.pingcap.com/tidb/dev/data-type-default-values#specify-expressions-as-default-values
        return True

    supports_table_check_constraints = property(
        operator.attrgetter("supports_column_check_constraints")
    )

    @cached_property
    def can_introspect_check_constraints(self):
        return False

    @cached_property
    def has_select_for_update_skip_locked(self):
        return False

    @cached_property
    def has_select_for_update_nowait(self):
        return False

    @cached_property
    def has_select_for_update_of(self):
        return False

    @cached_property
    def supports_explain_analyze(self):
        return True

    @cached_property
    def supported_explain_formats(self):
        return {"TRADITIONAL", "ROW", "BRIEF", "DOT", "TIDB_JSON"}

    @cached_property
    def ignores_table_name_case(self):
        return self.connection.tidb_server_data["lower_case_table_names"]

    @cached_property
    def supports_default_in_lead_lag(self):
        return True

    @cached_property
    def supports_json_field(self):
        return self.connection.tidb_version >= (
            6,
            3,
        )

    @cached_property
    def can_introspect_json_field(self):
        return self.supports_json_field and self.can_introspect_check_constraints

    @cached_property
    def supports_index_column_ordering(self):
        return False

    @cached_property
    def supports_expression_indexes(self):
        return self.connection.tidb_version >= (
            5,
            1,
        )
