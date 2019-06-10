from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

import election.serializers as serializers
from election.models import Election, Token, Vote
from libs import majority_judgment as mj


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = serializers.ElectionCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        election = serializer.save()
        for email in serializer.validated_data.get("elector_emails", []):
            if election.on_invitation_only:
                token = Token.objects.create(
                    election=election,
                    email=email,
                )
                print(
                    "Send mail : id election: %s, token: %s, email: %s"
                    %(election.id, token.id, email)
                )
            else:
                print("Send mail: id election: %s, email: %s"
                    %(election.id, email)
                )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ElectionDetailsAPIView(RetrieveAPIView):
    serializer_class = serializers.ElectionViewSerializer
    queryset = Election.objects.all()


class VoteAPIView(CreateAPIView):
    serializer_class = serializers.VoteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        election = serializer.validated_data["election"]

        if election.on_invitation_only:
            try:
                token = serializer.validated_data["token"]
            except KeyError:
                return Response(
                    "election on invitation only, please provide token",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                token_object = Token.objects.get(
                    election=election,
                    id=token,
                )
            except Token.DoesNotExist:
                return Response(
                    "wrong token",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if token_object.used:
                return Response(
                    "token already used",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token_object.used = True
            token_object.save()


        # Dealing with potential errors like the number of mentions
        # differs from the number of candidates.
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(status=status.HTTP_201_CREATED, headers=headers)




class ResultAPIView(APIView):
    """ 
    View to list the result of an election using majority judgment.
    """


    def create(self, request, *args, **kwargs):

        election = request.data.get("election", "")

        try:
           election = Election.objects.get(id=election)
        except Election.DoesNotExist:
            return Response(
                "unknown election",
                status=status.HTTP_400_BAD_REQUEST,
            )

        votes = Vote.objects.filter(election=election)
        scores = mj.votes_to_grades([v.grades_by_candidate for v in votes], \
                                    election.num_grades)
        ranks = mj.majority_judgment(scores)
        
        candidates = [Candidate(n, r, v) for n, r, v in \
                        zip(election.candidates, ranks, votes)]
        serializer = CandidateSerializer(candidates, many=True)    
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
