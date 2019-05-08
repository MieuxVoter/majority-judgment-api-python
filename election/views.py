from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from election.serializers import ElectionSerializer
# Create your views here.


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = ElectionSerializer
