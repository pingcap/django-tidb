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


# TiDBVersion deal with tidb's version string.
# Our tidb version string is got from ```select version();```
# it look like this:
#    5.7.25-TiDB-v5.1.0-64-gfb0eaf7b4
# or 5.7.25-TiDB-v5.2.0-alpha-385-g0f0b06ab5
class TiDBVersion:
    _version = (0, 0, 0)

    def match(self, version):
        version_list = version.split("-")
        if len(version_list) < 3:
            return False
        tidb_version_list = version_list[2].lstrip("v").split(".")
        self._version = tuple(int(x) for x in tidb_version_list)
        return True

    @property
    def version(self):
        return self._version
