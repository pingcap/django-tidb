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

import django
from django.db.backends.mysql.features import (
    DatabaseFeatures as MysqlDatabaseFeatures,
)
from django.utils.functional import cached_property


class DatabaseFeatures(MysqlDatabaseFeatures):
    has_select_for_update = True
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
    }

    minimum_database_version = (4,)

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
                # "Expression #5 of SELECT list is not in GROUP BY clause and contains nonaggregated column
                # 'test_django_tests.aggregation_regress_alfa.id' which is not functionally dependent on columns in
                # GROUP BY clause; this is incompatible with sql_mode=only_full_group_by"
                "aggregation.tests.AggregateTestCase.test_annotate_defer_select_related",
                "aggregation_regress.tests.AggregationTests.test_aggregate_duplicate_columns_select_related",
                "aggregation_regress.tests.AggregationTests.test_boolean_conversion",
                "aggregation_regress.tests.AggregationTests.test_more_more",
                "aggregation_regress.tests.JoinPromotionTests.test_ticket_21150",
                "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_aggregate_with_m2o",
                # Designed for MySQL only
                "backends.mysql.test_features.TestFeatures.test_supports_transactions",
                "check_framework.test_database.DatabaseCheckTests.test_mysql_strict_mode",
                # Unsupported add column and foreign key in single statement
                "indexes.tests.SchemaIndexesMySQLTests.test_no_index_for_foreignkey",
                "queries.test_explain.ExplainTests",
                "queries.test_qs_combinators.QuerySetSetOperationTests."
                "test_union_with_values_list_and_order_on_annotation",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_union_with_values_list_and_order",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_subqueries",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_by_f_expression_and_alias",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_by_f_expression",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_by_alias",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_order_by_same_type",
                "queries.test_qs_combinators.QuerySetSetOperationTests.test_combining_multiple_models",
                # is unrelation with tidb
                "file_uploads.tests.DirectoryCreationTests.test_readonly_root",
                "cache.tests.CacheMiddlewareTest.test_cache_page_timeout",
                # wrong test result
                ".test_no_duplicates_for_non_unique_related_object_in_search_fields",
                "transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_does_not_affect_outer",
                # TiDB does not support `JSON` format for `EXPLAIN ANALYZE`
                "queries.test_explain.ExplainTests.test_mysql_analyze",
                "queries.test_explain.ExplainTests.test_mysql_text_to_traditional",
                # TiDB cannot guarantee to always rollback the main thread txn when deadlock occurs
                "transactions.tests.AtomicMySQLTests.test_implicit_savepoint_rollback",
                "filtered_relation.tests.FilteredRelationTests.test_select_for_update",
                "filtered_relation.tests.FilteredRelationTests.test_union",
                "fixtures_regress.tests.TestFixtures.test_loaddata_raises_error_when_fixture_has_invalid_foreign_key",
                "introspection.tests.IntrospectionTests.test_get_table_description_nullable",
                # django.db.transaction.TransactionManagementError: An error occurred in the current transaction. You
                # can't execute queries until the end of the 'atomic' block.
                "transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_rolled_back_with_outer",
                "transaction_hooks.tests.TestConnectionOnCommit.test_discards_hooks_from_rolled_back_savepoint",
                "transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_rolled_back_with_outer",
                # AssertionError: True is not false
                "sites_tests.tests.CreateDefaultSiteTests.test_multi_db_with_router",
                # AssertionError: {} != {'example2.com': <Site: example2.com>}
                "sites_tests.tests.SitesFrameworkTests.test_clear_site_cache_domain",
                # AttributeError: 'NoneType' object has no attribute 'ping'
                "servers.test_liveserverthread.LiveServerThreadTest.test_closes_connections",
                # [planner:3065]Expression #1 of ORDER BY clause is not in SELECT list, references column '' which is
                # not in SELECT list; this is incompatible with
                "ordering.tests.OrderingTests.test_orders_nulls_first_on_filtered_subquery",
                # You have an error in your SQL syntax
                "schema.tests.SchemaTests.test_func_index_cast",
                "schema.tests.SchemaTests.test_add_field_binary",
                "schema.tests.SchemaTests.test_add_textfield_default_nullable",
                "schema.tests.SchemaTests.test_add_textfield_unhashable_default",
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
                # wrong result
                "schema.tests.SchemaTests.test_alter_pk_with_self_referential_field",
                # Unsupported add foreign key reference to themselves
                "schema.tests.SchemaTests.test_add_inline_fk_update_data",
                "schema.tests.SchemaTests.test_db_table",
                "schema.tests.SchemaTests.test_inline_fk",
                "schema.tests.SchemaTests.test_remove_constraints_capital_letters",
                "schema.tests.SchemaTests.test_rename_column_renames_deferred_sql_references",
                "schema.tests.SchemaTests.test_rename_referenced_field",
                "schema.tests.SchemaTests.test_rename_table_renames_deferred_sql_references",
                "schema.tests.SchemaTests.test_add_field_remove_field",
                # Unknown column 'annotations_publisher.id' in 'where clause'
                "annotations.tests.NonAggregateAnnotationTestCase.test_annotation_filter_with_subquery",
                # Duplicate entry 'admin' for key 'username'
                "auth_tests.test_admin_multidb.MultiDatabaseTests.test_add_view",
                # Duplicate entry 'app_b-examplemodelb' for key 'django_content_type_app_label_model_76bd3d3b_uniq'
                "auth_tests.test_models.LoadDataWithNaturalKeysAndMultipleDatabasesTestCase"
                ".test_load_data_with_user_permissions",
                "auth_tests.test_views.ChangelistTests.test_view_user_password_is_readonly",
                "auth_tests.test_migrations.MultiDBProxyModelAppLabelTests",
                "auth_tests.test_management.GetDefaultUsernameTestCase.test_with_database",
                "backends.base.test_base.ExecuteWrapperTests.test_nested_wrapper_invoked",
                "backends.base.test_base.ExecuteWrapperTests.test_outer_wrapper_blocks",
                "backends.tests.BackendTestCase.test_queries_limit",
                "backends.tests.FkConstraintsTests.test_check_constraints",
                "backends.tests.FkConstraintsTests.test_check_constraints_sql_keywords",
                # ignore multi database
                "contenttypes_tests.test_models.ContentTypesMultidbTests.test_multidb",
                # ContentType matching query does not exist.
                "contenttypes_tests.test_models.ContentTypesTests.test_app_labeled_name",
                # IntegrityError not raised
                "constraints.tests.CheckConstraintTests.test_database_constraint",
                "constraints.tests.CheckConstraintTests.test_database_constraint_unicode",
                # Cannot assign "<Book: Book object (90)>": the current database router prevents this relation.
                "prefetch_related.tests.MultiDbTests.test_using_is_honored_custom_qs",
                # django.http.response.Http404: No Article matches the given query.
                "get_object_or_404.tests.GetObjectOr404Tests.test_get_object_or_404",
                # django.db.transaction.TransactionManagementError: An error occurred in the current transaction.
                # You can't execute queries until the end of the 'atomic' block.
                "get_or_create.tests.UpdateOrCreateTests.test_integrity",
                "get_or_create.tests.UpdateOrCreateTests.test_manual_primary_key_test",
                "get_or_create.tests.UpdateOrCreateTestsWithManualPKs.test_create_with_duplicate_primary_key",
                "db_functions.text.test_chr.ChrTests.test_non_ascii",
                "db_functions.text.test_sha224.SHA224Tests.test_basic",
                "db_functions.text.test_sha224.SHA224Tests.test_transform",
                "db_functions.text.test_sha256.SHA256Tests.test_basic",
                "db_functions.text.test_sha256.SHA256Tests.test_transform",
                "db_functions.text.test_sha384.SHA384Tests.test_basic",
                "db_functions.text.test_sha384.SHA384Tests.test_transform",
                "db_functions.text.test_sha512.SHA512Tests.test_basic",
                "db_functions.text.test_sha512.SHA512Tests.test_transform",
                "db_functions.comparison.test_greatest.GreatestTests.test_basic",
                "db_functions.comparison.test_least.LeastTests.test_basic",
                "db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_time_func",
                "migrations.test_commands.MigrateTests.test_migrate_fake_initial_case_insensitive",
                "migrations.test_commands.MigrateTests.test_migrate_fake_split_initial",
                "migrations.test_commands.MigrateTests.test_migrate_plan",
                "migrations.test_executor.ExecutorTests.test_alter_id_type_with_fk",
                "migrations.test_operations.OperationTests.test_add_binaryfield",
                "migrations.test_operations.OperationTests.test_add_textfield",
                "migrations.test_operations.OperationTests.test_alter_field_pk",
                "migrations.test_operations.OperationTests.test_alter_field_reloads_state_on_fk_target_changes",
                "migrations.test_operations.OperationTests.test_autofield__bigautofield_foreignfield_growth",
                "migrations.test_operations.OperationTests.test_rename_field_reloads_state_on_fk_target_changes",
                "migrations.test_operations.OperationTests.test_smallfield_autofield_foreignfield_growth",
                "migrations.test_operations.OperationTests.test_smallfield_bigautofield_foreignfield_growth",
                # Unsupported modifying the Reorg-Data types on the primary key
                "migrations.test_operations.OperationTests.test_alter_field_pk_fk",
                "migrations.test_loader.RecorderTests.test_apply",
                "migrations.test_commands.MigrateTests.test_migrate_fake_initial",
                "migrations.test_commands.MigrateTests.test_migrate_initial_false",
                "migrations.test_commands.MigrateTests.test_migrate_syncdb_app_label",
                "migrations.test_commands.MigrateTests.test_migrate_syncdb_deferred_sql_executed_with_schemaeditor",
                "migrations.test_operations.OperationTests.test_add_constraint",
                "migrations.test_operations.OperationTests.test_add_constraint_combinable",
                "migrations.test_operations.OperationTests.test_add_constraint_percent_escaping",
                "migrations.test_operations.OperationTests.test_add_or_constraint",
                "migrations.test_operations.OperationTests.test_create_model_with_constraint",
                "migrations.test_operations.OperationTests.test_remove_constraint",
                # An error occurred in the current transaction. You can't execute queries until the end of the
                # 'atomic' block." not found in 'Save with update_fields did not affect any rows.
                "basic.tests.SelectOnSaveTests.test_select_on_save_lying_update",
                "admin_views.test_multidb.MultiDatabaseTests.test_add_view",
                "admin_views.test_multidb.MultiDatabaseTests.test_change_view",
                "admin_views.test_multidb.MultiDatabaseTests.test_delete_view",
                "admin_views.test_autocomplete_view.AutocompleteJsonViewTests.test_to_field_resolution_with_fk_pk",
                "admin_views.test_autocomplete_view.AutocompleteJsonViewTests.test_to_field_resolution_with_mti",
                "admin_views.tests.AdminSearchTest.test_exact_matches",
                "admin_views.tests.AdminSearchTest.test_no_total_count",
                "admin_views.tests.AdminSearchTest.test_search_on_sibling_models",
                "admin_views.tests.GroupAdminTest.test_group_permission_performance",
                "admin_views.tests.UserAdminTest.test_user_permission_performance",
                "multiple_database.tests.AuthTestCase.test_dumpdata",
                # about Pessimistic/Optimistic Transaction Model
                "select_for_update.tests.SelectForUpdateTests.test_raw_lock_not_available",
                # https://code.djangoproject.com/ticket/33627#ticket
                "model_forms.tests.ModelMultipleChoiceFieldTests.test_model_multiple_choice_field",
                # https://code.djangoproject.com/ticket/33633#ticket
                # once supports_transactions is True, could be opened; same as below
                "test_utils.test_testcase.TestDataTests.test_class_attribute_identity",
                "test_utils.tests.CaptureOnCommitCallbacksTests.test_execute",
                "test_utils.tests.CaptureOnCommitCallbacksTests.test_no_arguments",
                "test_utils.tests.CaptureOnCommitCallbacksTests.test_pre_callback",
                "test_utils.tests.CaptureOnCommitCallbacksTests.test_using",
                "test_utils.tests.TestBadSetUpTestData.test_failure_in_setUpTestData_should_rollback_transaction",
            },
        }
        if django.VERSION[0] > 3:
            skips.update(
                {
                    "django4": {
                        # MySQL needs a explicit CAST to ensure consistent results
                        "aggregation.tests.AggregateTestCase.test_aggregation_default_using_time_from_python",
                        "aggregation.tests.AggregateTestCase.test_aggregation_default_using_date_from_python",
                        "aggregation.tests.AggregateTestCase.test_aggregation_default_using_datetime_from_python",
                        "migrations.test_operations.OperationTests.test_alter_field_pk_mti_and_fk_to_base",
                        "migrations.test_operations.OperationTests.test_alter_field_pk_mti_fk",
                        # https://code.djangoproject.com/ticket/33633#ticket
                        # once supports_transactions is True, could be opened
                        "test_utils.test_testcase.TestTestCase.test_reset_sequences",
                        "test_utils.tests.CaptureOnCommitCallbacksTests.test_execute_recursive",
                        "test_utils.tests.CaptureOnCommitCallbacksTests.test_execute_tree",
                    }
                }
            )
        if django.VERSION < (4, 2):
            skips.update(
                {
                    "django4.1": {
                        # removed after Django 4.1
                        "defer_regress.tests.DeferAnnotateSelectRelatedTest.test_defer_annotate_select_related",
                    }
                }
            )
        if self.connection.tidb_version < (6,):
            skips.update(
                {
                    "tidb_lt6": {
                        "tidb.test_tidb_explain.TiDBExplainTests",
                        "schema.tests.SchemaTests.test_remove_indexed_field",
                    }
                }
            )
        if self.connection.tidb_version == (5, 0, 3):
            skips.update(
                {
                    "tidb503": {
                        "expressions_window.tests.WindowFunctionTests.test_subquery_row_range_rank",
                        "schema.tests.SchemaTests.test_alter_textual_field_keep_null_status",
                        # Unsupported modify column: column type conversion
                        # between 'varchar' and 'non-varchar' is currently unsupported yet
                        "schema.tests.SchemaTests.test_alter",
                        "schema.tests.SchemaTests.test_alter_field_type_and_db_collation",
                        "schema.tests.SchemaTests.test_alter_textual_field_keep_null_status",
                    }
                }
            )
        if self.connection.tidb_version == (4, 0, 0):
            skips.update(
                {
                    "tidb400": {
                        "admin_filters.tests.ListFiltersTests.test_relatedfieldlistfilter_reverse_relationships",
                        "admin_filters.tests.ListFiltersTests.test_emptylistfieldfilter_reverse_relationships",
                        "aggregation.test_filter_argument.FilteredAggregateTests.test_filtered_numerical_aggregates",
                        "aggregation_regress.tests.AggregationTests.test_stddev",
                        "aggregation_regress.tests.AggregationTests.test_aggregate_fexpr",
                        "annotations.tests.NonAggregateAnnotationTestCase.test_raw_sql_with_inherited_field",
                        "auth_tests.test_models.UserWithPermTestCase.test_basic",
                        "generic_relations_regress.tests.GenericRelationTests.test_ticket_20378",
                        "queries.test_bulk_update.BulkUpdateNoteTests.test_functions",
                        "queries.tests.TestTicket24605.test_ticket_24605",
                        "queries.tests.Queries6Tests.test_tickets_8921_9188",
                        "schema.tests.SchemaTests.test_add_field_default_nullable",
                    }
                }
            )
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
        if self.connection.tidb_version >= (
            4,
            0,
            5,
        ) and self.connection.tidb_version <= (4, 0, 9):
            skips["tidb4"].add("lookup.tests.LookupTests.test_regex")
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
        if django.utils.version.get_complete_version() < (4, 1):
            skips.update(
                {
                    "django40": {
                        "constraints.tests.CheckConstraintTests.test_database_constraint_expression",
                        "constraints.tests.CheckConstraintTests.test_database_constraint_expressionwrapper",
                        # 'Unsupported modify column: this column has primary key flag
                        "schema.tests.SchemaTests.test_alter_autofield_pk_to_smallautofield_pk_sequence_owner",
                        "test_utils.test_testcase.TestDataTests.test_undeepcopyable_warning",
                        # RuntimeError: A durable atomic block cannot be nested within another atomic block.
                        "transactions.tests.DisableDurabiltityCheckTests.test_nested_both_durable",
                        "transactions.tests.DisableDurabiltityCheckTests.test_nested_inner_durable",
                    }
                }
            )
        if django.utils.version.get_complete_version() >= (4, 1):
            skips.update(
                {
                    "django41": {
                        # Designed for MySQL only
                        "backends.mysql.tests.Tests.test_check_database_version_supported",
                        "backends.mysql.test_introspection.StorageEngineTests.test_get_storage_engine",
                        "migrations.test_operations.OperationTests.test_create_model_with_boolean_expression_in_check_constraint",
                        "migrations.test_operations.OperationTests.test_remove_func_unique_constraint",
                        "migrations.test_operations.OperationTests.test_remove_func_index",
                        "migrations.test_operations.OperationTests.test_alter_field_with_func_index",
                        "migrations.test_operations.OperationTests.test_add_func_unique_constraint",
                        "migrations.test_operations.OperationTests.test_add_func_index",
                        "schema.tests.SchemaTests.test_add_auto_field",
                        "schema.tests.SchemaTests.test_alter_autofield_pk_to_smallautofield_pk",
                        "schema.tests.SchemaTests.test_alter_primary_key_db_collation",
                        "schema.tests.SchemaTests.test_alter_primary_key_the_same_name",
                        "schema.tests.SchemaTests.test_autofield_to_o2o",
                        "schema.tests.SchemaTests.test_func_index_lookups",
                        "schema.tests.SchemaTests.test_func_unique_constraint_lookups",
                        "update.tests.AdvancedTests.test_update_ordered_by_inline_m2m_annotation",
                        "update.tests.AdvancedTests.test_update_ordered_by_m2m_annotation",
                        # Unsupported modifying collation of column from 'utf8mb4_general_ci' to 'utf8mb4_bin'
                        # when index is defined on it.
                        "migrations.test_operations.OperationTests.test_alter_field_pk_fk_db_collation",
                    }
                }
            )
        if django.utils.version.get_complete_version() >= (4, 2):
            skips.update(
                {
                    "django42": {
                        # Unsupported modifying the Reorg-Data types on the primary key
                        "migrations.test_operations.OperationTests.test_alter_field_pk_fk_char_to_int",
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
