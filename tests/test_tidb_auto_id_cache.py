import re

from django.db import models, connection
from django.db.utils import ProgrammingError
from django.test import TransactionTestCase
from django.test.utils import isolate_apps


AUTO_ID_CACHE_PATTERN = re.compile(r"\/\*T!\[auto_id_cache\] AUTO_ID_CACHE=(\d+) \*\/")


class TiDBAutoIDCacheTests(TransactionTestCase):
    available_apps = ["tidb"]

    def get_auto_id_cache_info(self, table):
        with connection.cursor() as cursor:
            cursor.execute(
                # It seems that SHOW CREATE TABLE is the only way to get the auto_random info.
                # Use parameterized query will add quotes to the table name, which will cause syntax error.
                f"SHOW CREATE TABLE {table}",
            )
            row = cursor.fetchone()
            if row is None:
                return None
            match = AUTO_ID_CACHE_PATTERN.search(row[1])
            if match:
                return match.groups()[0]
            return None

    @isolate_apps("tidb")
    def test_create_table_with_tidb_auto_id_cache_1(self):
        class AutoIDCacheNode1(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"
                tidb_auto_id_cache = 1

        with connection.schema_editor() as editor:
            editor.create_model(AutoIDCacheNode1)
        self.assertEqual(
            self.get_auto_id_cache_info(AutoIDCacheNode1._meta.db_table), "1"
        )

    @isolate_apps("tidb")
    def test_create_table_with_tidb_auto_id_cache_non_1(self):
        class AutoIDCacheNode2(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"
                tidb_auto_id_cache = 10

        with connection.schema_editor() as editor:
            editor.create_model(AutoIDCacheNode2)
        self.assertEqual(
            self.get_auto_id_cache_info(AutoIDCacheNode2._meta.db_table), "10"
        )

    @isolate_apps("tidb")
    def test_create_table_with_invalid_tidb_auto_id_cache(self):
        class AutoIDCacheNode3(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"
                tidb_auto_id_cache = "invalid"

        with self.assertRaises(ProgrammingError):
            with connection.schema_editor() as editor:
                editor.create_model(AutoIDCacheNode3)

    @isolate_apps("tidb")
    def test_create_table_without_tidb_auto_id_cache(self):
        class AutoIDCacheNode4(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(AutoIDCacheNode4)
        self.assertIsNone(self.get_auto_id_cache_info(AutoIDCacheNode4._meta.db_table))
