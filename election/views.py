from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from election.serializers import ElectionSerializer
# Create your views here.


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = ElectionSerializer

class ElectionResultsAPIView(APIView):
    def get(self, *args, **kwargs):
        ret = {}
        ret['data'] = 'results'
        return Response(ret)

class ElectionDetailsAPIView(APIView):
    def get(self, *args, **kwargs):
        ret = {}
        ret['data'] = 'details'
        return Response(ret)
