from django.db import models

from django_tidb.fields.vector import VectorField


class Document(models.Model):
    content = models.TextField()
    embedding = VectorField()


class DocumentExplicitDimension(models.Model):
    content = models.TextField()
    embedding = VectorField(dimensions=3)
