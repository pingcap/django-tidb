from unittest import TestCase, mock

from django.db import connection

from django_tidb.base import DatabaseWrapper
from django_tidb.version import TiDBVersion


class TiDBVersionTests(TestCase):
    def assert_version(self, version_string, expected):
        version = TiDBVersion()

        self.assertTrue(version.match(version_string))
        self.assertEqual(version.version, expected)

    def test_self_managed_stable_version(self):
        versions = (
            ("5.7.25-TiDB-v5.1.0-64-gfb0eaf7b4", (5, 1, 0)),
            ("8.0.11-TiDB-v8.5.5", (8, 5, 5)),
        )

        for version_string, expected in versions:
            with self.subTest(version_string=version_string):
                self.assert_version(version_string, expected)

    def test_self_managed_prerelease_version(self):
        self.assert_version(
            "5.7.25-TiDB-v5.2.0-alpha-385-g0f0b06ab5",
            (5, 2, 0),
        )

    def test_cloud_version(self):
        self.assert_version(
            "8.0.11-TiDB-CLOUD.202603.9",
            (202603, 9),
        )

    def test_invalid_versions(self):
        invalid_versions = (
            "",
            "8.0.11",
        )

        for version_string in invalid_versions:
            with self.subTest(version_string=version_string):
                self.assertFalse(TiDBVersion().match(version_string))


class DatabaseWrapperVersionTests(TestCase):
    def make_wrapper(self, version_string):
        wrapper = DatabaseWrapper(connection.settings_dict.copy())
        # Skip the query to the server.
        wrapper.__dict__["tidb_server_info"] = version_string
        return wrapper

    def test_version_is_not_shared_between_connections(self):
        first = self.make_wrapper("8.0.11-TiDB-v8.5.5")
        second = self.make_wrapper("5.7.25-TiDB-v6.5.9")
        original_match = TiDBVersion.match

        # Resolve the second connection's version while the first one is
        # between match() and reading .version, as another thread could.
        def match_and_interleave(version, version_string):
            result = original_match(version, version_string)
            if version_string == first.tidb_server_info:
                self.assertEqual(second.tidb_version, (6, 5, 9))
            return result

        with mock.patch.object(
            TiDBVersion, "match", autospec=True, side_effect=match_and_interleave
        ):
            self.assertEqual(first.tidb_version, (8, 5, 5))
