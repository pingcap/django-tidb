import json

from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection, transaction

from .models import Course


class TiDBExplainTests(TestCase):
    SUPPORTED_FORMATS = {"TRADITIONAL", "ROW", "BRIEF", "DOT", "TIDB_JSON"}

    def test_explain_with_supported_format(self):
        for format in self.SUPPORTED_FORMATS:
            with self.subTest(format=format), transaction.atomic():
                with CaptureQueriesContext(connection) as captured_queries:
                    result = Course.objects.filter(name="test").explain(format=format)
                    self.assertTrue(
                        captured_queries[0]["sql"].startswith(
                            connection.ops.explain_prefix + f' FORMAT="{format}"'
                        )
                    )
                    if format == "TIDB_JSON":
                        try:
                            json.loads(result)
                        except json.JSONDecodeError as e:
                            self.fail(
                                f"QuerySet.explain() result is not valid JSON: {e}"
                            )

    def test_explain_analyze_with_supported_format(self):
        for format in self.SUPPORTED_FORMATS:
            with self.subTest(format=format), transaction.atomic():
                with CaptureQueriesContext(connection) as captured_queries:
                    result = Course.objects.filter(name="test").explain(
                        analyze=True, format=format
                    )
                    self.assertTrue(
                        captured_queries[0]["sql"].startswith(
                            connection.ops.explain_prefix
                            + f' ANALYZE FORMAT="{format}"'
                        )
                    )
                    if format == "TIDB_JSON":
                        try:
                            json.loads(result)
                        except json.JSONDecodeError as e:
                            self.fail(
                                f"QuerySet.explain() result is not valid JSON: {e}"
                            )

    def test_explain_with_unsupported_format(self):
        with self.assertRaises(ValueError):
            Course.objects.filter(name="test").explain(format="JSON")

    def test_explain_analyze_with_unsupported_format(self):
        with self.assertRaises(ValueError):
            Course.objects.filter(name="test").explain(analyze=True, format="JSON")

    def test_explain_with_unkonwn_option(self):
        with self.assertRaises(ValueError):
            Course.objects.filter(name="test").explain(unknown_option=True)

    def test_explain_with_default_params(self):
        with transaction.atomic():
            with CaptureQueriesContext(connection) as captured_queries:
                Course.objects.filter(name="test").explain()
                self.assertTrue(
                    captured_queries[0]["sql"].startswith(
                        connection.ops.explain_prefix + ' FORMAT="ROW"'
                    )
                )
