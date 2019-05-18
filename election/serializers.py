from rest_framework import serializers
from election.models import Election

from django.utils.text import slugify


class ElectionViewMixin:
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["slug"] = slugify(instance.title)
        ret["id"] = instance.id
        return ret

class ElectionCreateSerializer(ElectionViewMixin, serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ('title', 'candidates')

class ElectionViewSerializer(ElectionViewMixin, serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = '__all__'

