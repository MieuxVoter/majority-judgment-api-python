from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from election.models import Election, Vote
import election.serializers as serializers


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = serializers.ElectionCreateSerializer


class ElectionDetailsAPIView(RetrieveAPIView):
    serializer_class = serializers.ElectionViewSerializer
    queryset = Election.objects.all()

class VoteAPIView(CreateAPIView):
    serializer_class = serializers.VoteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Dealing with potential errors like the number of mentions
        # differs from the number of candidates.
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(status=status.HTTP_201_CREATED, headers=headers)
