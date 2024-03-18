import re
from contextlib import contextmanager

from django.db import models, connection
from django.core import checks, validators
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase, override_settings
from django.test.utils import isolate_apps

from django_tidb.fields import BigAutoRandomField
from .models import BigAutoRandomModel, BigAutoRandomExplicitInsertModel


class TiDBBigAutoRandomFieldTests(TestCase):
    model = BigAutoRandomModel
    explicit_insert_model = BigAutoRandomExplicitInsertModel
    documented_range = (-9223372036854775808, 9223372036854775807)
    rel_db_type_class = BigAutoRandomField

    @contextmanager
    def explicit_insert_allowed(self):
        with connection.cursor() as cursor:
            cursor.execute("SET @@allow_auto_random_explicit_insert=true")
            yield
            cursor.execute("SET @@allow_auto_random_explicit_insert=false")

    @property
    def backend_range(self):
        field = self.model._meta.get_field("value")
        internal_type = field.get_internal_type()
        return connection.ops.integer_field_range(internal_type)

    def test_documented_range(self):
        """
        Values within the documented safe range pass validation, and can be
        saved and retrieved without corruption.
        """
        min_value, max_value = self.documented_range

        with self.explicit_insert_allowed():
            instance = self.explicit_insert_model(value=min_value)
            instance.full_clean()
            instance.save()
            qs = self.explicit_insert_model.objects.filter(value__lte=min_value)
            self.assertEqual(qs.count(), 1)
            self.assertEqual(qs[0].value, min_value)

            instance = self.explicit_insert_model(value=max_value)
            instance.full_clean()
            instance.save()
            qs = self.explicit_insert_model.objects.filter(value__gte=max_value)
            self.assertEqual(qs.count(), 1)
            self.assertEqual(qs[0].value, max_value)

    def test_backend_range_save(self):
        """
        Backend specific ranges can be saved without corruption.
        """
        min_value, max_value = self.backend_range
        with self.explicit_insert_allowed():
            if min_value is not None:
                instance = self.explicit_insert_model(value=min_value)
                instance.full_clean()
                instance.save()
                qs = self.explicit_insert_model.objects.filter(value__lte=min_value)
                self.assertEqual(qs.count(), 1)
                self.assertEqual(qs[0].value, min_value)

            if max_value is not None:
                instance = self.explicit_insert_model(value=max_value)
                instance.full_clean()
                instance.save()
                qs = self.explicit_insert_model.objects.filter(value__gte=max_value)
                self.assertEqual(qs.count(), 1)
                self.assertEqual(qs[0].value, max_value)

    def test_backend_range_validation(self):
        """
        Backend specific ranges are enforced at the model validation level
        (#12030).
        """
        min_value, max_value = self.backend_range

        if min_value is not None:
            instance = self.model(value=min_value - 1)
            expected_message = validators.MinValueValidator.message % {
                "limit_value": min_value,
            }
            with self.assertRaisesMessage(ValidationError, expected_message):
                instance.full_clean()
            instance.value = min_value
            instance.full_clean()

        if max_value is not None:
            instance = self.model(value=max_value + 1)
            expected_message = validators.MaxValueValidator.message % {
                "limit_value": max_value,
            }
            with self.assertRaisesMessage(ValidationError, expected_message):
                instance.full_clean()
            instance.value = max_value
            instance.full_clean()

    def test_redundant_backend_range_validators(self):
        """
        If there are stricter validators than the ones from the database
        backend then the backend validators aren't added.
        """
        min_backend_value, max_backend_value = self.backend_range

        for callable_limit in (True, False):
            with self.subTest(callable_limit=callable_limit):
                if min_backend_value is not None:
                    min_custom_value = min_backend_value + 1
                    limit_value = (
                        (lambda: min_custom_value)
                        if callable_limit
                        else min_custom_value
                    )
                    ranged_value_field = self.model._meta.get_field("value").__class__(
                        validators=[validators.MinValueValidator(limit_value)]
                    )
                    field_range_message = validators.MinValueValidator.message % {
                        "limit_value": min_custom_value,
                    }
                    with self.assertRaisesMessage(
                        ValidationError, "[%r]" % field_range_message
                    ):
                        ranged_value_field.run_validators(min_backend_value - 1)

                if max_backend_value is not None:
                    max_custom_value = max_backend_value - 1
                    limit_value = (
                        (lambda: max_custom_value)
                        if callable_limit
                        else max_custom_value
                    )
                    ranged_value_field = self.model._meta.get_field("value").__class__(
                        validators=[validators.MaxValueValidator(limit_value)]
                    )
                    field_range_message = validators.MaxValueValidator.message % {
                        "limit_value": max_custom_value,
                    }
                    with self.assertRaisesMessage(
                        ValidationError, "[%r]" % field_range_message
                    ):
                        ranged_value_field.run_validators(max_backend_value + 1)

    def test_types(self):
        instance = self.model(tag="a")
        instance.save()
        self.assertIsInstance(instance.value, int)
        instance = self.model.objects.get()
        self.assertIsInstance(instance.value, int)

    def test_invalid_value(self):
        tests = [
            (TypeError, ()),
            (TypeError, []),
            (TypeError, {}),
            (TypeError, set()),
            (TypeError, object()),
            (TypeError, complex()),
            (ValueError, "non-numeric string"),
            (ValueError, b"non-numeric byte-string"),
        ]
        for exception, value in tests:
            with self.subTest(value):
                msg = "Field 'value' expected a number but got %r." % (value,)
                with self.assertRaisesMessage(exception, msg):
                    self.explicit_insert_model.objects.create(value=value)

    def test_rel_db_type(self):
        field = self.model._meta.get_field("value")
        rel_db_type = field.rel_db_type(connection)
        # Currently, We can't find a general way to get the auto_random info from the field.
        self.assertEqual(rel_db_type, "bigint")
        if connection.tidb_version < (6, 3):
            self.assertEqual(
                self.rel_db_type_class().db_type(connection), "bigint AUTO_RANDOM(5)"
            )
        else:
            self.assertEqual(
                self.rel_db_type_class().db_type(connection),
                "bigint AUTO_RANDOM(5, 64)",
            )


AUTO_RANDOM_PATTERN = re.compile(
    r"\/\*T!\[auto_rand\] AUTO_RANDOM\((\d+)(?:, (\d+))?\) \*\/"
)


class TiDBAutoRandomMigrateTests(TransactionTestCase):
    available_apps = ["tidb"]

    def get_primary_key(self, table):
        with connection.cursor() as cursor:
            primary_key_columns = connection.introspection.get_primary_key_columns(
                cursor, table
            )
            return primary_key_columns[0] if primary_key_columns else None

    def get_auto_random_info(self, table):
        # return (shard_bits, range)
        with connection.cursor() as cursor:
            cursor.execute(
                # It seems that SHOW CREATE TABLE is the only way to get the auto_random info.
                # Use parameterized query will add quotes to the table name, which will cause syntax error.
                f"SHOW CREATE TABLE {table}",
            )
            row = cursor.fetchone()
            if row is None:
                return (None, None)
            for line in row[1].splitlines():
                match = AUTO_RANDOM_PATTERN.search(line)
                if match:
                    return match.groups()
            return (None, None)

    @isolate_apps("tidb")
    @override_settings(DEFAULT_AUTO_FIELD="django_tidb.fields.BigAutoRandomField")
    def test_create_table_with_default_auto_field(self):
        class AutoRandomNode1(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(AutoRandomNode1)
        self.assertEqual(self.get_primary_key(AutoRandomNode1._meta.db_table), "id")
        self.assertIsInstance(AutoRandomNode1._meta.pk, BigAutoRandomField)
        self.assertEqual(
            self.get_auto_random_info(AutoRandomNode1._meta.db_table), ("5", None)
        )

    @isolate_apps("tidb")
    def test_create_table_explicit_auto_random_field(self):
        class AutoRandomNode2(models.Model):
            id = BigAutoRandomField(primary_key=True)
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(AutoRandomNode2)
        self.assertEqual(self.get_primary_key(AutoRandomNode2._meta.db_table), "id")
        self.assertIsInstance(AutoRandomNode2._meta.pk, BigAutoRandomField)
        self.assertEqual(
            self.get_auto_random_info(AutoRandomNode2._meta.db_table), ("5", None)
        )

    @isolate_apps("tidb")
    def test_create_table_explicit_auto_random_field_with_shard_bits(self):
        class AutoRandomNode3(models.Model):
            id = BigAutoRandomField(primary_key=True, shard_bits=10)
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(AutoRandomNode3)
        self.assertEqual(self.get_primary_key(AutoRandomNode3._meta.db_table), "id")
        self.assertIsInstance(AutoRandomNode3._meta.pk, BigAutoRandomField)
        self.assertEqual(
            self.get_auto_random_info(AutoRandomNode3._meta.db_table), ("10", None)
        )

    @isolate_apps("tidb")
    def test_create_table_explicit_auto_random_field_with_shard_bits_and_range(self):
        class AutoRandomNode4(models.Model):
            id = BigAutoRandomField(primary_key=True, shard_bits=10, range=60)
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(AutoRandomNode4)
        self.assertEqual(self.get_primary_key(AutoRandomNode4._meta.db_table), "id")
        self.assertIsInstance(AutoRandomNode4._meta.pk, BigAutoRandomField)
        self.assertEqual(
            self.get_auto_random_info(AutoRandomNode4._meta.db_table), ("10", "60")
        )

    @isolate_apps("tidb")
    def test_create_table_explicit_auto_random_field_with_range(self):
        class AutoRandomNode5(models.Model):
            id = BigAutoRandomField(primary_key=True, range=60)
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(AutoRandomNode5)
        self.assertEqual(self.get_primary_key(AutoRandomNode5._meta.db_table), "id")
        self.assertIsInstance(AutoRandomNode5._meta.pk, BigAutoRandomField)
        self.assertEqual(
            self.get_auto_random_info(AutoRandomNode5._meta.db_table), ("5", "60")
        )

    @isolate_apps("tidb")
    def test_create_table_explicit_auto_random_field_with_invalid_range(self):
        class AutoRandomNode6(models.Model):
            id = BigAutoRandomField(primary_key=True, range=31)

            class Meta:
                app_label = "tidb"

        id = AutoRandomNode6._meta.get_field("id")
        self.assertEqual(
            id.check(),
            [
                checks.Error(
                    "BigAutoRandomField 'range' attribute must be an integer between 32 and 64.",
                    obj=id,
                )
            ],
        )

        class AutoRandomNode7(models.Model):
            id = BigAutoRandomField(primary_key=True, range=None)

            class Meta:
                app_label = "tidb"

        id = AutoRandomNode7._meta.get_field("id")
        self.assertEqual(
            id.check(),
            [
                checks.Error(
                    "BigAutoRandomField must define a 'range' attribute.",
                    obj=id,
                )
            ],
        )

    @isolate_apps("tidb")
    def test_create_table_explicit_auto_random_field_with_invalid_shard_bits(self):
        class AutoRandomNode8(models.Model):
            id = BigAutoRandomField(primary_key=True, shard_bits=16)

            class Meta:
                app_label = "tidb"

        id = AutoRandomNode8._meta.get_field("id")
        self.assertEqual(
            id.check(),
            [
                checks.Error(
                    "BigAutoRandomField 'shard_bits' attribute must be an integer between 1 and 15.",
                    obj=id,
                )
            ],
        )

        class AutoRandomNode9(models.Model):
            id = BigAutoRandomField(primary_key=True, shard_bits=None)

            class Meta:
                app_label = "tidb"

        id = AutoRandomNode9._meta.get_field("id")
        self.assertEqual(
            id.check(),
            [
                checks.Error(
                    "BigAutoRandomField must define a 'shard_bits' attribute.",
                    obj=id,
                )
            ],
        )
