from typing import Optional
from time import time
from django.db import IntegrityError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
import election.serializers as serializers
from election.models import Election, Token, Vote
from libs import majority_judgment as mj
 
# Error codes:
UNKNOWN_ELECTION_ERROR = "E1: Unknown election"
ONGOING_ELECTION_ERROR = "E2: Ongoing election"
NO_VOTE_ERROR = "E3: No recorded vote"
ELECTION_NOT_STARTED_ERROR = "E4: Election not started"
ELECTION_FINISHED_ERROR = "E5: Election finished"
INVITATION_ONLY_ERROR = "E6: Election on invitation only, please provide token"
UNKNOWN_TOKEN_ERROR = "E7: Wrong token"
USED_TOKEN_ERROR = "E8: Token already used"
WRONG_ELECTION_ERROR = "E9: Parameters for the election are incorrect"


def send_mail_invitation(email: str, election: str, token_id: Optional[int] = None):   
    token_get: str = f"?token={token_id}" if token_id is not None else ""
    merge_data = {
        "invitation_url": f"{settings.SITE_URL}/vote/{election.id}{token_get}",
        "result_url": f"{settings.SITE_URL}/result/{election.id}",
        "title": election.title,
        }
    text_body = render_to_string(
        f"election/{election.select_language}_mail_invitation.txt",
        merge_data
    )
    html_body = render_to_string(
        f"election/{election.select_language}_mail_invitation.html",
        merge_data
    )   
    msg = EmailMultiAlternatives(
        election.title,
        text_body,
        settings.EMAIL_HOST_USER,
        [email])
    msg.attach_alternative(html_body, "text/html")
    msg.send()


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = serializers.ElectionCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        election = serializer.save()
        electors_emails = serializer.validated_data.get("elector_emails", [])
        for email in electors_emails:
            if election.on_invitation_only:
                token = Token.objects.create(
                    election=election,
                    email=email,
                )
                print(
                    "Send mail : id election: %s, token: %s, email: %s"
                    %(election.id, token.id, email)
                )
                send_mail_invitation(email, election, token_id=token.id)
            else:
                send_mail_invitation(email, election)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ElectionDetailsAPIView(RetrieveAPIView):
    serializer_class = serializers.ElectionViewSerializer

    def get(self, request, pk, **kwargs):

        try:
            election = Election.objects.get(id=pk)
        except Election.DoesNotExist:
            return Response(
                UNKNOWN_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if round(time()) < election.start_at:
            return Response(
                ELECTION_NOT_STARTED_ERROR,
                status=status.HTTP_401_UNAUTHORIZED,                
            
            )
        if round(time()) >= election.finish_at:
            return Response(
                ELECTION_FINISHED_ERROR,
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        serializer = serializers.ElectionViewSerializer(election)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
        
    queryset = Election.objects.all()


class VoteAPIView(CreateAPIView):
    serializer_class = serializers.VoteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        election = serializer.validated_data["election"]

        # TODO this feature is not yet implement in the front 
        # if election.on_invitation_only:
        if False:
            try:
                token = serializer.validated_data["token"]
            except KeyError:
                return Response(
                    INVITATION_ONLY_ERROR,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                token_object = Token.objects.get(
                    election=election,
                    id=token,
                )
            except Token.DoesNotExist:
                return Response(
                    UNKNOWN_TOKEN_ERROR,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if token_object.used:
                return Response(
                    USED_TOKEN_ERROR,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token_object.used = True
            token_object.save()


        # Dealing with potential errors like the number of mentions
        # differs from the number of candidates.
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                WRONG_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST
            )
        headers = self.get_success_headers(serializer.data)
        return Response(status=status.HTTP_201_CREATED, headers=headers)




class ResultAPIView(APIView):
    """
    View to list the result of an election using majority judgment.
    """

    def get(self, request, pk, **kwargs):

        try:
            election = Election.objects.get(id=pk)
        except Election.DoesNotExist:
            return Response(
                UNKNOWN_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                WRONG_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (election.restrict_results and round(time()) < election.finish_at):
            return Response(
                ONGOING_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )

        votes = Vote.objects.filter(election=election)

        if len(votes) == 0:
            return Response(
                NO_VOTE_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )

        profiles, scores, grades, sorted_indexes = mj.compute_votes(
            [v.grades_by_candidate for v in votes],
            election.num_grades
        )

        candidates = [
            serializers.Candidate(
                election.candidates[idx],
                idx,
                profiles[idx],
                grades[idx],
                scores[idx],
                len(votes)
            )
            for idx in sorted_indexes
        ]
        serializer = serializers.CandidateSerializer(candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
