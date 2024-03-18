import numpy as np
from django.core import checks
from django import forms
from django.db.models import Field, FloatField, Func, Value

MAX_DIM_LENGTH = 16000
MIN_DIM_LENGTH = 1


def encode_vector(value, dim=None):
    if value is None:
        return value

    if isinstance(value, np.ndarray):
        if value.ndim != 1:
            raise ValueError("expected ndim to be 1")

        if not np.issubdtype(value.dtype, np.integer) and not np.issubdtype(
            value.dtype, np.floating
        ):
            raise ValueError("dtype must be numeric")

        value = value.tolist()

    if dim is not None and len(value) != dim:
        raise ValueError("expected %d dimensions, not %d" % (dim, len(value)))

    return "[" + ",".join([str(float(v)) for v in value]) + "]"


def decode_vector(value):
    if value is None or isinstance(value, np.ndarray):
        return value

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    return np.array(value[1:-1].split(","), dtype=np.float32)


class VectorField(Field):
    """
    Support for AI Vector storage.

    Status: Beta

    Info: https://www.pingcap.com/blog/integrating-vector-search-into-tidb-for-ai-applications/

    Example:
    ```python
    from django.db import models
    from django_tidb.fields.vector import VectorField, CosineDistance

    class Document(models.Model):
        content = models.TextField()
        embedding = VectorField(dimensions=3)

    # Create a document
    Document.objects.create(
        content="test content",
        embedding=[1, 2, 3],
    )

    # Query with distance
    Document.objects.alias(
        distance=CosineDistance('embedding', [3, 1, 2])
    ).filter(distance__lt=5)
    ```
    """

    description = "Vector"
    empty_strings_allowed = False

    def __init__(self, *args, dimensions=None, **kwargs):
        self.dimensions = dimensions
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.dimensions is not None:
            kwargs["dimensions"] = self.dimensions
        return name, path, args, kwargs

    def db_type(self, connection):
        if self.dimensions is None:
            return "vector<float>"
        return "vector<float>(%d)" % self.dimensions

    def from_db_value(self, value, expression, connection):
        return decode_vector(value)

    def to_python(self, value):
        if isinstance(value, list):
            return np.array(value, dtype=np.float32)
        return decode_vector(value)

    def get_prep_value(self, value):
        return encode_vector(value)

    def value_to_string(self, obj):
        return self.get_prep_value(self.value_from_object(obj))

    def validate(self, value, model_instance):
        if isinstance(value, np.ndarray):
            value = value.tolist()
        super().validate(value, model_instance)

    def run_validators(self, value):
        if isinstance(value, np.ndarray):
            value = value.tolist()
        super().run_validators(value)

    def formfield(self, **kwargs):
        return super().formfield(form_class=VectorFormField, **kwargs)

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_dimensions(),
        ]

    def _check_dimensions(self):
        if self.dimensions is not None and (
            self.dimensions < MIN_DIM_LENGTH or self.dimensions > MAX_DIM_LENGTH
        ):
            return [
                checks.Error(
                    f"Vector dimensions must be in the range [{MIN_DIM_LENGTH}, {MAX_DIM_LENGTH}]",
                    obj=self,
                )
            ]
        return []


class DistanceBase(Func):
    output_field = FloatField()

    def __init__(self, expression, vector, **extra):
        if not hasattr(vector, "resolve_expression"):
            vector = Value(encode_vector(vector))
        super().__init__(expression, vector, **extra)


class L1Distance(DistanceBase):
    function = "VEC_L1_DISTANCE"


class L2Distance(DistanceBase):
    function = "VEC_L2_DISTANCE"


class CosineDistance(DistanceBase):
    function = "VEC_COSINE_DISTANCE"


class NegativeInnerProduct(DistanceBase):
    function = "VEC_NEGATIVE_INNER_PRODUCT"


class VectorWidget(forms.TextInput):
    def format_value(self, value):
        if isinstance(value, np.ndarray):
            value = value.tolist()
        return super().format_value(value)


class VectorFormField(forms.CharField):
    widget = VectorWidget

    def has_changed(self, initial, data):
        if isinstance(initial, np.ndarray):
            initial = initial.tolist()
        return super().has_changed(initial, data)
