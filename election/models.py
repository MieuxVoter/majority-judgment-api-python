from django.db import models
from django.contrib.postgres.fields import ArrayField
from libs.django_randomprimary import RandomPrimaryIdModel


class Election(RandomPrimaryIdModel):
    title = models.CharField("Title", max_length=255)
    candidates = ArrayField(models.CharField("Name", max_length=255), default=list)
