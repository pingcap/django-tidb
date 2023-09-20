from django.db import models

from django_tidb.fields import BigAutoRandomField


class Course(models.Model):
    name = models.CharField(max_length=100)


class BigAutoRandomModel(models.Model):
    value = BigAutoRandomField(primary_key=True)
    tag = models.CharField(max_length=100, blank=True, null=True)


class BigAutoRandomExplicitInsertModel(models.Model):
    value = BigAutoRandomField(primary_key=True)
    tag = models.CharField(max_length=100, blank=True, null=True)
