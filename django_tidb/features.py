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
    supports_transactions = False
    uses_savepoints = False
    can_release_savepoints = False
    atomic_transactions = False
    supports_atomic_references_rename = False
    can_clone_databases = False
    can_rollback_ddl = False
    order_by_nulls_first = True
    supports_foreign_keys = False
    indexes_foreign_keys = False
    test_collations = {
        'ci': 'utf8mb4_general_ci',
        'non_default': 'utf8mb4_unicode_ci',
    }

    @cached_property
    def django_test_skips(self):
        skips = {
            "This doesn't work on MySQL.": {
                'db_functions.comparison.test_greatest.GreatestTests.test_coalesce_workaround',
                'db_functions.comparison.test_least.LeastTests.test_coalesce_workaround',
            },
            'Running on MySQL requires utf8mb4 encoding (#18392).': {
                'model_fields.test_textfield.TextFieldTests.test_emoji',
                'model_fields.test_charfield.TestCharField.test_emoji',
            },
            "MySQL doesn't support functional indexes on a function that "
            "returns JSON": {
                'schema.tests.SchemaTests.test_func_index_json_key_transform',
            },
            "MySQL supports multiplying and dividing DurationFields by a "
            "scalar value but it's not implemented (#25287).": {
                'expressions.tests.FTimeDeltaTests.test_durationfield_multiply_divide',
            },
            "tidb": {
                # "Expression #5 of SELECT list is not in GROUP BY clause and contains nonaggregated column
                # 'test_django_tests.aggregation_regress_alfa.id' which is not functionally dependent on columns in
                # GROUP BY clause; this is incompatible with sql_mode=only_full_group_by"
                'aggregation.tests.AggregateTestCase.test_annotate_defer_select_related',

                'aggregation_regress.tests.AggregationTests.test_aggregate_duplicate_columns_select_related',
                'aggregation_regress.tests.AggregationTests.test_boolean_conversion',
                'aggregation_regress.tests.AggregationTests.test_more_more',
                'aggregation_regress.tests.JoinPromotionTests.test_ticket_21150',
                'annotations.tests.NonAggregateAnnotationTestCase.test_annotation_aggregate_with_m2o',
                'defer_regress.tests.DeferAnnotateSelectRelatedTest.test_defer_annotate_select_related',

                'lookup.tests.LookupTests.test_regex',

                'queries.test_explain.ExplainTests',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_union_with_values_list_and_order_on_annotation',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_union_with_values_list_and_order',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_subqueries',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_by_f_expression_and_alias',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_by_f_expression',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering_by_alias',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_ordering',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_order_by_same_type',
                'queries.test_qs_combinators.QuerySetSetOperationTests.test_combining_multiple_models',

                # is unrelation with tidb
                'file_uploads.tests.DirectoryCreationTests.test_readonly_root',
                'cache.tests.CacheMiddlewareTest.test_cache_page_timeout',

                # RuntimeError: A durable atomic block cannot be nested within another atomic block.
                'transactions.tests.DisableDurabiltityCheckTests.test_nested_both_durable',
                'transactions.tests.DisableDurabiltityCheckTests.test_nested_inner_durable',

                # wrong test result
                '.test_no_duplicates_for_non_unique_related_object_in_search_fields',
                'transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_does_not_affect_outer',
                'filtered_relation.tests.FilteredRelationTests.test_select_for_update',
                'filtered_relation.tests.FilteredRelationTests.test_union',
                'fixtures_regress.tests.TestFixtures.test_loaddata_raises_error_when_fixture_has_invalid_foreign_key',
                'introspection.tests.IntrospectionTests.test_get_table_description_nullable',

                # django.db.transaction.TransactionManagementError: An error occurred in the current transaction. You
                # can't execute queries until the end of the 'atomic' block.
                'transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_rolled_back_with_outer',
                'transaction_hooks.tests.TestConnectionOnCommit.test_discards_hooks_from_rolled_back_savepoint',
                'transaction_hooks.tests.TestConnectionOnCommit.test_inner_savepoint_rolled_back_with_outer',

                # AssertionError: True is not false
                'sites_tests.tests.CreateDefaultSiteTests.test_multi_db_with_router',
                # AssertionError: {} != {'example2.com': <Site: example2.com>}
                'sites_tests.tests.SitesFrameworkTests.test_clear_site_cache_domain',

                # AttributeError: 'NoneType' object has no attribute 'ping'
                'servers.test_liveserverthread.LiveServerThreadTest.test_closes_connections',

                'test_utils.tests.TestBadSetUpTestData.test_failure_in_setUpTestData_should_rollback_transaction',
                'test_utils.test_testcase.TestDataTests.test_undeepcopyable_warning',
                'test_utils.test_testcase.TestDataTests.test_class_attribute_identity',
                'test_utils.tests.CaptureOnCommitCallbacksTests.test_execute',
                'test_utils.tests.CaptureOnCommitCallbacksTests.test_no_arguments',
                'test_utils.tests.CaptureOnCommitCallbacksTests.test_pre_callback',
                'test_utils.tests.CaptureOnCommitCallbacksTests.test_using',

                # [planner:3065]Expression #1 of ORDER BY clause is not in SELECT list, references column '' which is
                # not in SELECT list; this is incompatible with
                'ordering.tests.OrderingTests.test_orders_nulls_first_on_filtered_subquery',

                # You have an error in your SQL syntax
                'schema.tests.SchemaTests.test_func_index_cast',
                'schema.tests.SchemaTests.test_add_field_binary',
                'schema.tests.SchemaTests.test_add_textfield_default_nullable',
                'schema.tests.SchemaTests.test_add_textfield_unhashable_default',

                # Unsupported modify column: this column has primary key flag
                'schema.tests.SchemaTests.test_alter_auto_field_to_char_field',

                # Unsupported modify column: can't remove auto_increment without @@tidb_allow_remove_auto_inc enabled
                'schema.tests.SchemaTests.test_alter_auto_field_to_integer_field',

                # 'Unsupported modify column: this column has primary key flag
                'schema.tests.SchemaTests.test_alter_autofield_pk_to_smallautofield_pk_sequence_owner',

                # Found wrong number (0) of check constraints for schema_author.height
                'schema.tests.SchemaTests.test_alter_field_default_dropped',

                # Unsupported modify column: can't set auto_increment
                'schema.tests.SchemaTests.test_alter_int_pk_to_autofield_pk',
                'schema.tests.SchemaTests.test_alter_int_pk_to_bigautofield_pk',

                # Unsupported drop primary key when the table's pkIsHandle is true
                'schema.tests.SchemaTests.test_alter_int_pk_to_int_unique',

                # Unsupported drop integer primary key
                'schema.tests.SchemaTests.test_alter_not_unique_field_to_primary_key',

                # Unsupported modify column: can't set auto_increment
                'schema.tests.SchemaTests.test_alter_smallint_pk_to_smallautofield_pk',

                # BLOB/TEXT/JSON column 'address' can't have a default value
                'schema.tests.SchemaTests.test_alter_text_field_to_not_null_with_default_value',

                # Unsupported modify column: this column has primary key flag
                'schema.tests.SchemaTests.test_char_field_pk_to_auto_field',

                # Unsupported modify charset from utf8mb4 to utf8
                'schema.tests.SchemaTests.test_ci_cs_db_collation',

                # Unsupported drop integer primary key
                'schema.tests.SchemaTests.test_primary_key',

                # wrong result
                'schema.tests.SchemaTests.test_alter_pk_with_self_referential_field',
                'schema.tests.SchemaTests.test_db_table',
                'schema.tests.SchemaTests.test_indexes',
                'schema.tests.SchemaTests.test_inline_fk',
                'schema.tests.SchemaTests.test_remove_constraints_capital_letters',
                'schema.tests.SchemaTests.test_remove_db_index_doesnt_remove_custom_indexes',
                'schema.tests.SchemaTests.test_rename_column_renames_deferred_sql_references',
                'schema.tests.SchemaTests.test_rename_referenced_field',
                'schema.tests.SchemaTests.test_rename_table_renames_deferred_sql_references',
                'schema.tests.SchemaTests.test_add_field_remove_field',

                # Unknown column 'annotations_publisher.id' in 'where clause'
                'annotations.tests.NonAggregateAnnotationTestCase.test_annotation_filter_with_subquery',

                # Duplicate entry 'admin' for key 'username'
                'auth_tests.test_admin_multidb.MultiDatabaseTests.test_add_view',

                # Duplicate entry 'app_b-examplemodelb' for key 'django_content_type_app_label_model_76bd3d3b_uniq'
                'auth_tests.test_models.LoadDataWithNaturalKeysAndMultipleDatabasesTestCase'
                '.test_load_data_with_user_permissions',

                'auth_tests.test_views.ChangelistTests.test_view_user_password_is_readonly',
                'auth_tests.test_migrations.MultiDBProxyModelAppLabelTests',
                'auth_tests.test_management.GetDefaultUsernameTestCase.test_with_database',

                # You have an error in your SQL syntax; check the manual that corresponds to your TiDB
                # version for the right syntax to use line 2 column 25 near "PROCEDURE test_procedure
                # (P_I INTEGER)\n        BEGIN\n            DECLARE V_I INTEGER;\n            SET V_I
                # = P_I;\n        END;\n    "
                'backends.test_utils.CursorWrapperTests.test_callproc_with_int_params',

                # You have an error in your SQL syntax; check the manual that corresponds to your TiDB
                # version for the right syntax to use line 2 column 25 near "PROCEDURE test_procedure ()\n
                # BEGIN\n            DECLARE V_I INTEGER;\n            SET V_I = 1;\n        END;\n    "
                'backends.test_utils.CursorWrapperTests.test_callproc_without_params',

                'backends.base.test_base.ExecuteWrapperTests.test_nested_wrapper_invoked',
                'backends.base.test_base.ExecuteWrapperTests.test_outer_wrapper_blocks',
                'backends.tests.FkConstraintsTests.test_check_constraints',
                'backends.tests.FkConstraintsTests.test_check_constraints_sql_keywords',

                # ignore multi database
                'contenttypes_tests.test_models.ContentTypesMultidbTests.test_multidb',

                # ContentType matching query does not exist. 
                'contenttypes_tests.test_models.ContentTypesTests.test_app_labeled_name',

                # IntegrityError not raised
                'constraints.tests.CheckConstraintTests.test_database_constraint',
                'constraints.tests.CheckConstraintTests.test_database_constraint_expression',
                'constraints.tests.CheckConstraintTests.test_database_constraint_expressionwrapper',
                'constraints.tests.CheckConstraintTests.test_database_constraint_unicode',

                # Cannot assign "<Book: Book object (90)>": the current database router prevents this relation.
                'prefetch_related.tests.MultiDbTests.test_using_is_honored_custom_qs',

                # django.http.response.Http404: No Article matches the given query.
                'get_object_or_404.tests.GetObjectOr404Tests.test_get_object_or_404',

                # django.db.transaction.TransactionManagementError: An error occurred in the current transaction.
                # You can't execute queries until the end of the 'atomic' block.
                'get_or_create.tests.UpdateOrCreateTests.test_integrity',
                'get_or_create.tests.UpdateOrCreateTests.test_manual_primary_key_test',
                'get_or_create.tests.UpdateOrCreateTestsWithManualPKs.test_create_with_duplicate_primary_key',

                'db_functions.text.test_chr.ChrTests.test_non_ascii',
                'db_functions.text.test_sha224.SHA224Tests.test_basic',
                'db_functions.text.test_sha224.SHA224Tests.test_transform',
                'db_functions.text.test_sha256.SHA256Tests.test_basic',
                'db_functions.text.test_sha256.SHA256Tests.test_transform',
                'db_functions.text.test_sha384.SHA384Tests.test_basic',
                'db_functions.text.test_sha384.SHA384Tests.test_transform',
                'db_functions.text.test_sha512.SHA512Tests.test_basic',
                'db_functions.text.test_sha512.SHA512Tests.test_transform',
                'db_functions.comparison.test_greatest.GreatestTests.test_basic',
                'db_functions.comparison.test_least.LeastTests.test_basic',
                'db_functions.datetime.test_extract_trunc.DateFunctionTests.test_trunc_time_func',
                'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_extract_func_with_timezone',
                'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_extract_func_with_timezone',
                'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests.test_trunc_time_func',
                'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests'
                '.test_trunc_timezone_applied_before_truncation',
                'db_functions.datetime.test_extract_trunc.DateFunctionWithTimeZoneTests'
                '.test_trunc_timezone_applied_before_truncation',
                'db_functions.text.test_reverse.ReverseTests.test_expressions',

                'migrations.test_commands.MigrateTests.test_migrate_fake_initial_case_insensitive',
                'migrations.test_commands.MigrateTests.test_migrate_fake_split_initial',
                'migrations.test_commands.MigrateTests.test_migrate_plan',
                'migrations.test_executor.ExecutorTests.test_alter_id_type_with_fk',
                'migrations.test_operations.OperationTests.test_add_binaryfield',
                'migrations.test_operations.OperationTests.test_add_textfield',
                'migrations.test_operations.OperationTests.test_alter_field_pk',
                'migrations.test_operations.OperationTests.test_alter_field_reloads_state_on_fk_target_changes',
                'migrations.test_operations.OperationTests.test_autofield__bigautofield_foreignfield_growth',
                'migrations.test_operations.OperationTests.test_rename_field_reloads_state_on_fk_target_changes',
                'migrations.test_operations.OperationTests.test_smallfield_autofield_foreignfield_growth',
                'migrations.test_operations.OperationTests.test_smallfield_bigautofield_foreignfield_growth',
                'migrations.test_loader.RecorderTests.test_apply',
                'migrations.test_commands.MigrateTests.test_migrate_fake_initial',
                'migrations.test_commands.MigrateTests.test_migrate_initial_false',
                'migrations.test_commands.MigrateTests.test_migrate_syncdb_app_label',
                'migrations.test_commands.MigrateTests.test_migrate_syncdb_deferred_sql_executed_with_schemaeditor',
                'migrations.test_operations.OperationTests.test_add_constraint',
                'migrations.test_operations.OperationTests.test_add_constraint_combinable',
                'migrations.test_operations.OperationTests.test_add_constraint_percent_escaping',
                'migrations.test_operations.OperationTests.test_add_or_constraint',
                'migrations.test_operations.OperationTests.test_create_model_with_constraint',
                'migrations.test_operations.OperationTests.test_remove_constraint',
                'model_fields.test_uuid.TestQuerying.test_icontains',
                'model_fields.test_uuid.TestQuerying.test_iendswith',
                'model_fields.test_uuid.TestQuerying.test_iexact',
                'model_fields.test_uuid.TestQuerying.test_istartswith',

                # An error occurred in the current transaction. You can't execute queries until the end of the
                # 'atomic' block." not found in 'Save with update_fields did not affect any rows.
                'basic.tests.SelectOnSaveTests.test_select_on_save_lying_update',

                'admin_views.test_multidb.MultiDatabaseTests.test_add_view',
                'admin_views.test_multidb.MultiDatabaseTests.test_change_view',
                'admin_views.test_multidb.MultiDatabaseTests.test_delete_view',
                'admin_views.test_autocomplete_view.AutocompleteJsonViewTests.test_to_field_resolution_with_fk_pk',
                'admin_views.test_autocomplete_view.AutocompleteJsonViewTests.test_to_field_resolution_with_mti',
                'admin_views.tests.AdminSearchTest.test_exact_matches',
                'admin_views.tests.AdminSearchTest.test_no_total_count',
                'admin_views.tests.AdminSearchTest.test_search_on_sibling_models',
                'admin_views.tests.GroupAdminTest.test_group_permission_performance',
                'admin_views.tests.UserAdminTest.test_user_permission_performance',

                'multiple_database.tests.AuthTestCase.test_dumpdata',

                # about Pessimistic/Optimistic Transaction Model
                'select_for_update.tests.SelectForUpdateTests.test_raw_lock_not_available',
            }
        }
        return skips

    @cached_property
    def update_can_self_select(self):
        return True

    @cached_property
    def can_introspect_foreign_keys(self):
        return False

    @cached_property
    def can_return_columns_from_insert(self):
        return False

    can_return_rows_from_bulk_insert = property(operator.attrgetter('can_return_columns_from_insert'))

    @cached_property
    def has_zoneinfo_database(self):
        return self.connection.tidb_server_data['has_zoneinfo_database']

    @cached_property
    def is_sql_auto_is_null_enabled(self):
        return self.connection.tidb_server_data['sql_auto_is_null']

    @cached_property
    def supports_over_clause(self):
        return True

    supports_frame_range_fixed_distance = property(operator.attrgetter('supports_over_clause'))

    @cached_property
    def supports_column_check_constraints(self):
        return True

    supports_table_check_constraints = property(operator.attrgetter('supports_column_check_constraints'))

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
        return {'DOT', 'ROW', 'BRIEF'}

    @cached_property
    def ignores_table_name_case(self):
        return self.connection.tidb_server_data['lower_case_table_names']

    @cached_property
    def supports_default_in_lead_lag(self):
        return True

    @cached_property
    def supports_json_field(self):
        return False

    @cached_property
    def can_introspect_json_field(self):
        return self.supports_json_field and self.can_introspect_check_constraints

    @cached_property
    def supports_index_column_ordering(self):
        return False

    @cached_property
    def supports_expression_indexes(self):
        return self.connection.tidb_version >= (5, 1, )
