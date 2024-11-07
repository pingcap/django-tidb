import re

from django.db import models, connection
from django.test import TransactionTestCase
from django.test.utils import isolate_apps

TIFLASH_REPLICA_PATTERN = re.compile(r"\/\*T!\[tiflash_replica\] TIFLASH_REPLICA=(\d+) \*\/")

class TiDBTiFlashReplicaTests(TransactionTestCase):
    available_apps = ["tidb"]

    def get_tiflash_replica_info(self, table):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SHOW CREATE TABLE {table}",
            )
            row = cursor.fetchone()
            if row is None:
                return None
            match = TIFLASH_REPLICA_PATTERN.search(row[1])
            if match:
                return match.groups()[0]
            return None

    @isolate_apps("tidb")
    def test_create_table_without_tiflash_replica(self):
        class TiFlashReplicaNode0(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(TiFlashReplicaNode0)
        self.assertIsNone(self.get_tiflash_replica_info(TiFlashReplicaNode0._meta.db_table))

    @isolate_apps("tidb")
    def test_create_table_with_tiflash_replica_1(self):
        class TiFlashReplicaNode1(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"
                tiflash_replica = 1

        with connection.schema_editor() as editor:
            editor.create_model(TiFlashReplicaNode1)
        self.assertEqual(
            self.get_tiflash_replica_info(TiFlashReplicaNode1._meta.db_table), "1"
        )
