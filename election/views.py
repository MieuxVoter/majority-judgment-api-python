import os
import urllib
import base64

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


def send_mails_invitation_api(list_email_token: list, election: str):
    """
    Def to send the election invitation by API
    """

    for couple in list_email_token:
        token_get: str = f"?token={couple[1]}"
        merge_data: Dict[str, str] = {
            "invitation_url": f"{settings.SITE_URL}/vote/{election.id}{token_get}",
            "result_url": f"{settings.SITE_URL}/result/{election.id}",
            "title": election.title,
        }

        if election.select_language not in settings.LANGUAGE_AVAILABLE:
            activate(settings.DEFAULT_LANGUAGE)
        else:
            activate(election.select_language)

        text_body = render_to_string("election/mail_invitation.txt", merge_data)
        html_body = render_to_string("election/mail_invitation.html", merge_data)

        data = urllib.parse.urlencode(
            {
                "from": "Mieux Voter <" + settings.DEFAULT_FROM_EMAIL + ">",
                "to": couple[0],
                "subject": f"[{gettext('Mieux Voter')}] {election.title}",
                "text": text_body,
                "html": html_body,
                "o:tracking": False,
                "o:tag": "Invitation",
                "o:require-tls": settings.EMAIL_USE_TLS,
                "o:skip-verification": settings.EMAIL_SKIP_VERIFICATION,
            },
            doseq=True,
        ).encode()

        send_api(data)


def send_mail_api(email: str, text_body, html_body, title):
    """
    Def to send mails by API
    """
    data = urllib.parse.urlencode(
        {
            "from": "Mieux Voter <" + settings.DEFAULT_FROM_EMAIL + ">",
            "to": email,
            "subject": f"[{gettext('Mieux Voter')}] {title}",
            "text": text_body,
            "html": html_body,
            "o:tracking": False,
            "o:tag": "Invitation",
            "o:require-tls": settings.EMAIL_USE_TLS,
            "o:skip-verification": settings.EMAIL_SKIP_VERIFICATION,
        },
        doseq=True,
    ).encode()
    send_api(data)


def send_api(data):
    """
    def to do api request
    """
    request = urllib.request.Request(settings.EMAIL_API_DOMAIN, data=data)
    encoded_token = base64.b64encode(
        ("api:" + settings.EMAIL_API_KEY).encode("ascii")
    ).decode("ascii")
    request.add_header("Authorization", "Basic {}".format(encoded_token))
    try:
        urllib.request.urlopen(request)
    except Exception as err:
        return err


def send_mails_invitation_smtp(list_email_token: list, election: str):
    """
    Def to send the election invitation by SMTP
    """
    for couple in list_email_token:
        token_get: str = f"?token={couple[1]}"
        merge_data: Dict[str, str] = {
            "invitation_url": f"{settings.SITE_URL}/vote/{election.id}{token_get}",
            "result_url": f"{settings.SITE_URL}/result/{election.id}",
            "title": election.title,
        }

        if election.select_language not in settings.LANGUAGE_AVAILABLE:
            activate(settings.DEFAULT_LANGUAGE)
        else:
            activate(election.select_language)

        text_body = render_to_string("election/mail_invitation.txt", merge_data)
        html_body = render_to_string("election/mail_invitation.html", merge_data)

        msg = EmailMultiAlternatives(
            f"[{gettext('Mieux Voter')}] {election.title}",
            text_body,
            settings.EMAIL_HOST_USER,
            [couple[0]],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()


class ElectionCreateAPIView(CreateAPIView):
    serializer_class = serializers.ElectionCreateSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        election = serializer.save()
        electors_emails = serializer.validated_data.get("elector_emails", [])

        list_email_token = []
        for email in electors_emails:
            token = Token.objects.create(
                election=election,
            )
            list_email_token.append([email, token.id])

        if election.send_mail:
            if settings.EMAIL_TYPE == "API":
                send_mails_invitation_api(list_email_token, election)
            else:
                send_mails_invitation_smtp(list_email_token, election)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
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
    """
    View to vote in an election
    """

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
            return Response(WRONG_ELECTION_ERROR, status=status.HTTP_400_BAD_REQUEST)
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

        if election.restrict_results and round(time()) < election.finish_at:
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
        indexed_values: List[
            Tuple[int, mj.MajorityValue]
        ] = mj.sort_by_value_with_index(
            [mj.MajorityValue(profil) for profil in merit_profiles]
        )
        print(len(indexed_values))

        candidates = [
            serializers.Candidate(
                election.candidates[idx],
                idx,
                merit_profiles[idx],
                value.grade,
            )
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
        election_id = serializer.validated_data["election_id"]
        select_language = serializer.validated_data["select_language"]

        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            return Response(
                WRONG_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )

        emails = serializer.validated_data.get("emails", [])

        merge_data: Dict[str, str] = {
            "result_url": f"{settings.SITE_URL}/result/{election.id}",
            "title": election.title,
        }

        if (
            select_language == None
            or select_language not in settings.LANGUAGE_AVAILABLE
        ):
            select_language = election.select_language

        activate(select_language)

        if election.on_invitation_only:
            text_body = render_to_string("election/mail_one_link.txt", merge_data)
            html_body = render_to_string("election/mail_one_link.html", merge_data)

        else:
            merge_data["vote_url"] = f"{settings.SITE_URL}/vote/{election.id}"
            text_body = render_to_string("election/mail_two_links.txt", merge_data)
            html_body = render_to_string("election/mail_two_links.html", merge_data)

        send_status = send_mail_api(emails, text_body, html_body, election.title)

        return Response(status=send_status)
