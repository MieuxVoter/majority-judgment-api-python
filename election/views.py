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

from django.core.mail import send_mail


# Error codes:
UNKNOWN_ELECTION_ERROR = "E1: Unknown election"
ONGOING_ELECTION_ERROR = "E2: Ongoing election"
NO_VOTE_ERROR = "E3: No recorded vote"

def send_mail_invitation_old(email, election):   
    merge_data = {
        "invitation_url":settings.SITE_URL + "/vote/" + election.id,
        "result_url":settings.SITE_URL + "/result/" + election.id,
        "title": election.title,
        }
    text_body = render_to_string("election/mail_invitation.txt",merge_data)
    html_body = render_to_string("election/mail_invitation.html",merge_data)   
    msg = EmailMultiAlternatives(
        election.title,
        text_body,
        settings.EMAIL_HOST_USER,
        [ email ],
        fail_silently=False
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()

def send_mail_invitation(email,election):
    subject = "ceci est un test"
    message = "J'espère que ça fonctionne bien"
    send_mail(subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently = False)


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
                print(# TODO!
                    "Send mail : id election: %s, token: %s, email: %s"
                    %(election.id, token.id, email)
                )
                send_mail_invitation(email, election)
            else:
                send_mail_invitation(email, election)

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


    def get(self, request, pk, **kwargs):

        try:
            election = Election.objects.get(id=pk)
        except Election.DoesNotExist:
            return Response(
                UNKNOWN_ELECTION_ERROR,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not election.is_finished and not election.is_opened:
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

        profiles, scores, grades = mj.compute_votes([v.grades_by_candidate for v in votes],
                                    election.num_grades)
        sorted_indexes = mj.majority_judgment(profiles)
        #grades = [mj.majority_grade(profile) for profile in profiles]
        candidates = [serializers.Candidate(election.candidates[idx], idx, p, g, s)
                      for idx, p, s, g in zip(sorted_indexes, profiles, scores, grades)]
        serializer = serializers.CandidateSerializer(candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)