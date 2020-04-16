from django.utils.text import slugify
from rest_framework import serializers

from election.models import Election, Vote
from django.conf import settings


class ElectionViewMixin:

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["slug"] = slugify(instance.title)
        ret["id"] = instance.id
        return ret


class ElectionCreateSerializer(ElectionViewMixin, serializers.ModelSerializer):

    elector_emails = serializers.ListField(
        child=serializers.EmailField(),
        write_only=True,
        required=False,
    )

    def create(self, validated_data):
        # Copy the validated_data
        validated_data = dict(validated_data)
        try:
            validated_data.pop("elector_emails")
        except KeyError:
            pass

        return Election.objects.create(**validated_data)

    class Meta:
        model = Election
        fields = (
            'title',
            'candidates',
            'on_invitation_only',
            'num_grades',
            'elector_emails',
            'start_at',
            'finish_at',
        )


class ElectionViewSerializer(ElectionViewMixin, serializers.ModelSerializer):

    class Meta:
        model = Election
        fields = '__all__'


class VoteSerializer(serializers.ModelSerializer):

    grades_by_candidate = serializers.ListField(
        child=serializers.IntegerField(
            min_value=0,
            max_value=settings.MAX_NUM_GRADES - 1,
        )
    )

    token = serializers.CharField(write_only=True, required=False)

    def create(self, validated_data):
        # Copy the validated_data
        validated_data = dict(validated_data)
        try:
            validated_data.pop("token")
        except KeyError:
            pass

        return Vote.objects.create(**validated_data)

    class Meta:
        model = Vote
        fields = (
            'grades_by_candidate',
            'election',
            'token',
        )

# See https://github.com/MieuxVoter/mvapi/pull/5#discussion_r291891403 for explanations
class Candidate:
    def __init__(self, name, idx, profile, grade, score):
        self.name = name
        self.id = idx
        self.score = score
        self.profile = profile
        self.grade = grade

class CandidateSerializer(serializers.Serializer):
    name = serializers.CharField()
    id = serializers.IntegerField(min_value=0)
    score = serializers.FloatField(min_value=0, max_value=1)
    profile = serializers.ListField(child=serializers.IntegerField())
    grade = serializers.IntegerField(min_value=0, max_value=settings.MAX_NUM_GRADES)
