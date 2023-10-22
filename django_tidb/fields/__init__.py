from django.db.models import BigAutoField
from django.core import checks

__all__ = [
    "BigAutoRandomField",
]


class BigAutoRandomField(BigAutoField):
    def __init__(
        self,
        verbose_name=None,
        name=None,
        shard_bits=5,
        range=64,
        **kwargs,
    ):
        self.shard_bits, self.range = shard_bits, range
        super().__init__(verbose_name, name, **kwargs)

    def get_internal_type(self):
        return "BigAutoRandomField"

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_range(),
            *self._check_shard_bits(),
        ]

    def _check_shard_bits(self):
        try:
            shard_bits = int(self.shard_bits)
            if shard_bits < 1 or shard_bits > 15:
                raise ValueError()
        except TypeError:
            return [
                checks.Error(
                    "BigAutoRandomField must define a 'shard_bits' attribute.",
                    obj=self,
                )
            ]
        except ValueError:
            return [
                checks.Error(
                    "BigAutoRandomField 'shard_bits' attribute must be an integer between 1 and 15.",
                    obj=self,
                )
            ]
        else:
            return []

    def _check_range(self):
        try:
            range = int(self.range)
            if range < 32 or range > 64:
                raise ValueError()
        except TypeError:
            return [
                checks.Error(
                    "BigAutoRandomField must define a 'range' attribute.",
                    obj=self,
                )
            ]
        except ValueError:
            return [
                checks.Error(
                    "BigAutoRandomField 'range' attribute must be an integer between 32 and 64.",
                    obj=self,
                )
            ]
        else:
            return []

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.shard_bits is not None:
            kwargs["shard_bits"] = self.shard_bits
        if self.range is not None:
            kwargs["range"] = self.range
        return name, path, args, kwargs

    def db_type(self, connection):
        data = self.db_type_parameters(connection)
        if connection.tidb_version < (6, 3):
            # TiDB < 6.3 doesn't support define AUTO_RANDOM with range
            data_type = "bigint AUTO_RANDOM(%(shard_bits)s)"
        else:
            data_type = "bigint AUTO_RANDOM(%(shard_bits)s, %(range)s)"
        return data_type % data
