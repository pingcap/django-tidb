from django.test import TransactionTestCase
from django.test.utils import isolate_apps
from django.db import models, connection


class TiDBDDLTests(TransactionTestCase):
    available_apps = ["tidb"]

    def get_indexes(self, table):
        """
        Get the indexes on the table using a new cursor.
        """
        with connection.cursor() as cursor:
            return [
                c["columns"][0]
                for c in connection.introspection.get_constraints(
                    cursor, table
                ).values()
                if c["index"] and len(c["columns"]) == 1
            ]

    def get_uniques(self, table):
        with connection.cursor() as cursor:
            return [
                c["columns"][0]
                for c in connection.introspection.get_constraints(
                    cursor, table
                ).values()
                if c["unique"] and len(c["columns"]) == 1
            ]

    @isolate_apps("tidb")
    def test_should_create_db_index(self):
        # When define a model with db_index=True, TiDB should create a db index
        class Tag(models.Model):
            title = models.CharField(max_length=255, db_index=True)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(Tag)
        self.assertIn("title", self.get_indexes("tidb_tag"))

        new_field = models.CharField(max_length=255, db_index=True)
        new_field.set_attributes_from_name("new_field")
        with connection.schema_editor() as editor:
            editor.add_field(Tag, new_field)
        self.assertIn("new_field", self.get_indexes("tidb_tag"))

    @isolate_apps("tidb")
    def test_should_create_db_index_for_foreign_key_with_no_db_constraint(self):
        # When define a model with ForeignKey, TiDB should not create a db index
        class Node1(models.Model):
            title = models.CharField(max_length=255)

            class Meta:
                app_label = "tidb"

        class Node2(models.Model):
            node1 = models.ForeignKey(
                Node1, on_delete=models.CASCADE, db_constraint=False
            )

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(Node1)
            editor.create_model(Node2)

        self.assertIn("node1_id", self.get_indexes("tidb_node2"))

    @isolate_apps("tidb")
    def test_add_unique_field(self):
        # issue: https://github.com/pingcap/django-tidb/issues/48
        class Node3(models.Model):
            title = models.CharField(max_length=255, unique=True)

            class Meta:
                app_label = "tidb"

        with connection.schema_editor() as editor:
            editor.create_model(Node3)
        self.assertIn("title", self.get_uniques("tidb_node3"))

        new_field = models.CharField(max_length=255, unique=True)
        new_field.set_attributes_from_name("new_field")
        with connection.schema_editor() as editor:
            editor.add_field(Node3, new_field)
        self.assertIn("new_field", self.get_uniques("tidb_node3"))

        parent = models.OneToOneField(Node3, models.CASCADE)
        parent.set_attributes_from_name("parent")
        with connection.schema_editor() as editor:
            editor.add_field(Node3, parent)
        self.assertIn("parent_id", self.get_uniques("tidb_node3"))
