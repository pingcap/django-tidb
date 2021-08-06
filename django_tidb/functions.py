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

from django.db.models.fields.json import HasKeyLookup, KeyTransform
from django.db.models.functions import Random, Cast, Ord, Length, ConcatPair, Chr
from django.db.models.functions.mixins import FixDurationInputMixin
from django.db.models.functions.text import MySQLSHA2Mixin


def char(self, compiler, connection, **extra_context):
    return self.as_sql(
        compiler, connection, function='CHAR',
        template='%(function)s(%(expressions)s USING utf8mb4)',
        **extra_context
    )


def register_functions():
    """Register the above methods with the corersponding Django classes."""
    Random.as_tidb = Random.as_mysql
    HasKeyLookup.as_tidb = HasKeyLookup.as_mysql
    KeyTransform.as_tidb = KeyTransform.as_mysql
    Cast.as_tidb = Cast.as_mysql
    FixDurationInputMixin.as_tidb = FixDurationInputMixin.as_mysql
    Ord.as_tidb = Ord.as_mysql
    Length.as_tidb = Length.as_mysql
    ConcatPair.as_tidb = ConcatPair.as_mysql
    Chr.as_tidb = char
    MySQLSHA2Mixin.as_tidb = MySQLSHA2Mixin.as_mysql
