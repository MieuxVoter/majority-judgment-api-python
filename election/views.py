import os
from typing import Optional, Dict, Tuple, List
from time import time
from django.db import IntegrityError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import activate, gettext
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.request import Request
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
SEND_MAIL_ERROR = "E10: Error sending email"

# A Grade is always given a int
Grade = int 

def send_mail_invitation(
        email: str, election: str, token_id: int
    ):   
    token_get: str = f"?token={token_id}"
    merge_data: Dict[str, str] = {
        "invitation_url": f"{settings.SITE_URL}/vote/{election.id}{token_get}",
        "result_url": f"{settings.SITE_URL}/result/{election.id}",
        "title": election.title,
    }

    activate(
        election.select_language
        if election.select_language in os.environ.get("LANGUAGE_AVAILABLE", [])
        else "en"
    )

    text_body = render_to_string("election/mail_invitation.txt", merge_data)
    html_body = render_to_string("election/mail_invitation.html", merge_data)   

    msg = EmailMultiAlternatives(
        f"[{gettext('Mieux Voter')}] {election.title}",
        text_body,
        settings.EMAIL_HOST_USER,
        [email])
    msg.attach_alternative(html_body, "text/html")
    msg.send()


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = serializers.ElectionCreateSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        election = serializer.save()
        electors_emails = serializer.validated_data.get("elector_emails", [])
        for email in electors_emails:
            token = Token.objects.create(
                election=election,
                email=email,
            )
            send_mail_invitation(email, election, token.id)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class ElectionDetailsAPIView(RetrieveAPIView):
    serializer_class = serializers.ElectionViewSerializer

    def get(self, request: Request, pk: str, **kwargs) -> Response:

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
        
        serializer = serializers.ElectionViewSerializer(election)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
        

class VoteAPIView(CreateAPIView):
    serializer_class = serializers.VoteSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        election = serializer.validated_data["election"]

        if round(time()) >= election.finish_at:
            return Response(
                ELECTION_FINISHED_ERROR,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if election.on_invitation_only:
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

        votes: List[List[Grade]] = [v.grades_by_candidate for v in votes]

        merit_profiles: List[Dict[Grade, int]] = mj.votes_to_merit_profiles(
            votes, range(election.num_grades)
        )
        indexed_values: List[Tuple[int, mj.MajorityValue]] = mj.sort_by_value_with_index([
            mj.MajorityValue(profil) for profil in merit_profiles
        ])
        print(len(indexed_values))

        candidates = [
            serializers.Candidate(
                election.candidates[idx],
                idx,
                merit_profiles[idx],
                value.grade,
            )
            # for idx in sorted_indexes
            for idx, value in indexed_values
        ]
        serializer = serializers.CandidateSerializer(candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LinkAPIView(CreateAPIView):
    """
        View to send the result and vote links if it is an open election
    """
    serializer_class = serializers.LinkSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)        
        id_election = serializer.validated_data["id_election"]
        select_language = serializer.validated_data["select_language"]

        try:
            election = Election.objects.get(id=id_election)
        except Election.DoesNotExist:
            return Response(
                WRONG_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        creator_emails = serializer.validated_data.get("creator_emails",[])        
        
        if election.on_invitation_only:
            merge_data: Dict[str, str] = {
                "result_url": f"{settings.SITE_URL}/result/{election.id}",
                "title": election.title,
            }

            activate(
                select_language
                if select_language in os.environ.get("LANGUAGE_AVAILABLE", [])
                else "en"
            )

            text_body = render_to_string("election/mail_one_link.txt", merge_data)
            html_body = render_to_string("election/mail_one_link.html", merge_data)

            try:
                for email in creator_emails:
                    msg = EmailMultiAlternatives(
                        f"[{gettext('Mieux Voter')}] {election.title}",
                        text_body,
                        settings.EMAIL_HOST_USER,
                        [email])
                    msg.attach_alternative(html_body, "text/html")
                    msg.send()
            except:
                Response(
                    SEND_MAIL_ERROR,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            merge_data: Dict[str, str] = {
                "invitation_url": f"{settings.SITE_URL}/vote/{election.id}",
                "result_url": f"{settings.SITE_URL}/result/{election.id}",
                "title": election.title,
            }

            activate(
                select_language
                if select_language in os.environ.get("LANGUAGE_AVAILABLE", [])
                else "en"
            )

            text_body = render_to_string("election/mail_two_links.txt", merge_data)
            html_body = render_to_string("election/mail_two_links.html", merge_data)

            try:
                for email in creator_emails:
                    msg = EmailMultiAlternatives(
                        f"[{gettext('Mieux Voter')}] {election.title}",
                        text_body,
                        settings.EMAIL_HOST_USER,
                        [email])
                    msg.attach_alternative(html_body, "text/html")
                    msg.send()
            except:
                Response(
                    SEND_MAIL_ERROR,
                    status=status.HTTP_400_BAD_REQUEST,
                )
       

        headers = self.get_success_headers(serializer.data)
        return Response(status=status.HTTP_201_CREATED, headers=headers)

