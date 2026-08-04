from unittest import TestCase

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
