import numpy as np
from math import sqrt
from django.db.utils import OperationalError
from django.test import TestCase
from django_tidb.fields.vector import (
    CosineDistance,
    L1Distance,
    L2Distance,
    NegativeInnerProduct,
)

from .models import Document, DocumentExplicitDimension


class TiDBVectorFieldTests(TestCase):
    model = Document

    def test_create_get(self):
        obj = self.model.objects.create(
            content="test content",
            embedding=[1, 2, 3],
        )
        obj = self.model.objects.get(pk=obj.pk)
        self.assertTrue(np.array_equal(obj.embedding, np.array([1, 2, 3])))
        self.assertEqual(obj.embedding.dtype, np.float32)

    def test_get_with_different_dimension(self):
        self.model.objects.create(
            content="test content",
            embedding=[1, 2, 3],
        )
        with self.assertRaises(OperationalError) as cm:
            list(
                self.model.objects.annotate(
                    distance=CosineDistance("embedding", [3, 1, 2, 4])
                ).values_list("distance", flat=True)
            )
        self.assertIn("vectors have different dimensions", str(cm.exception))

    def create_documents(self):
        vectors = [[1, 1, 1], [2, 2, 2], [1, 1, 2]]
        for i, v in enumerate(vectors):
            self.model.objects.create(
                content=f"{i + 1}",
                embedding=v,
            )

    def test_l1_distance(self):
        self.create_documents()
        distance = L1Distance("embedding", [1, 1, 1])
        docs = self.model.objects.annotate(distance=distance).order_by("distance")
        self.assertEqual([d.content for d in docs], ["1", "3", "2"])
        self.assertEqual([d.distance for d in docs], [0, 1, 3])

    def test_l2_distance(self):
        self.create_documents()
        distance = L2Distance("embedding", [1, 1, 1])
        docs = self.model.objects.annotate(distance=distance).order_by("distance")
        self.assertEqual([d.content for d in docs], ["1", "3", "2"])
        self.assertEqual([d.distance for d in docs], [0, 1, sqrt(3)])

    def test_cosine_distance(self):
        self.create_documents()
        distance = CosineDistance("embedding", [1, 1, 1])
        docs = self.model.objects.annotate(distance=distance).order_by("distance")
        self.assertEqual([d.content for d in docs], ["1", "2", "3"])
        self.assertEqual([d.distance for d in docs], [0, 0, 0.05719095841793653])

    def test_negative_inner_product(self):
        self.create_documents()
        distance = NegativeInnerProduct("embedding", [1, 1, 1])
        docs = self.model.objects.annotate(distance=distance).order_by("distance")
        self.assertEqual([d.content for d in docs], ["2", "3", "1"])
        self.assertEqual([d.distance for d in docs], [-6, -4, -3])


class TiDBVectorFieldExplicitDimensionTests(TiDBVectorFieldTests):
    model = DocumentExplicitDimension
