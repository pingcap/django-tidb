#!/usr/bin/env python3

# Copyright 2020 Google LLC.

# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# NOTE: The code in this file is based on code from the
# googleapis/python-spanner-django project, licensed under BSD
#
# https://github.com/googleapis/python-spanner-django/blob/0544208d6f9ef81b290cf5c4ee304ba0ec0e95c4/run_testing_worker.py
#

# Copyright 2021 PingCAP, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import os
import random
import time
import subprocess

with open("django_test_apps.txt", "r") as file:
    all_apps = file.read().split("\n")

print("test apps: ", all_apps)

if not all_apps:
    exit()

time.sleep(3)

os.system(
    """DJANGO_TEST_APPS="{apps}" bash ./django_test_suite.sh""".format(
        apps=" ".join(all_apps)
    )
)
