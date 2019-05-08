from django.db import models

# Create your models here.

class Election(models.Model):
    title = models.CharField("Title", max_length=255)