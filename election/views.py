from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from election.models import Election
from election.serializers import ElectionSerializer


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = ElectionSerializer


class ElectionDetailsAPIView(RetrieveAPIView):
    serializer_class = ElectionSerializer
    queryset = Election.objects.all()
