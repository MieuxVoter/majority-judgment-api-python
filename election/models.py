from django.db import models
from libs.django_randomprimary import RandomPrimaryIdModel


class Election(RandomPrimaryIdModel):
    title = models.CharField("Title", max_length=255)
