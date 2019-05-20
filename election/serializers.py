from rest_framework import serializers
from election.models import Election, Vote, NUMBER_OF_MENTIONS

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


class VoteSerializer(serializers.ModelSerializer):
    mentions_by_candidate = serializers.ListField(
        child=serializers.IntegerField(
            min_value=0,
            max_value=NUMBER_OF_MENTIONS-1,
        )
    )

    class Meta:
        model = Vote
        fields = '__all__'
