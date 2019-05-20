from django.contrib import admin
from .models import Election, Vote

admin.site.register(Election)
admin.site.register(Vote)