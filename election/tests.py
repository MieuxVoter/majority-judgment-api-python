from django.test import TestCase
from rest_framework.test import APITestCase
from election.models import Election, Token, MAX_NUM_GRADES
import election.urls as urls
from mvapi.utils import majority_judgment
from election.utils import grades_matrix

import json



class ElectionCreateAPIViewTestCase(APITestCase):

    def test_create_election(self):
        title = "Super élection - utf-8 chars: 🤨 😐 😑 😶 🙄 😏 😣 😥 😮 🤐 😯 😪 😫 😴 😌 😛 😜 😝 🤤 😒 😓 😔 😕 🙃 🤑 😲 ☹️ 🙁 😖 😞 😟 😤 😢 😭 😦 😧 😨 😩 🤯 !"

        candidates = [
            "Seb",
            "Pierre-Louis",
        ]

        response_post = self.client.post(
            urls.new_election(),
            {
                "title": title,
                "candidates": candidates,
                "on_invitation_only": False,
            },
        )
        self.assertEqual(201, response_post.status_code)

        election_pk = response_post.data["id"]
        response_get = self.client.get(urls.election_details(election_pk))
        self.assertEqual(200, response_get.status_code)
        self.assertEqual(title, response_get.data["title"])
        self.assertEqual(candidates, response_get.data["candidates"])

class VoteCreateAPIViewTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.election = Election.objects.create(
            title="Test election",
            candidates=[
                "Seb",
                "Pierre-Louis",
            ]
        )

    def test_valid_vote(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [0, 1],
            }
        )

        self.assertEqual(201, response.status_code)

    def test_too_many_grades(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [0, 1, 0],
            }
        )

        self.assertEqual(400, response.status_code)

    def test_too_few_grades(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [1],
            }
        )

        self.assertEqual(400, response.status_code)

    def test_mention_too_high(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [0, MAX_NUM_GRADES],
            }
        )

        self.assertEqual(400, response.status_code)

    def test_mention_too_low(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [0, -1],
            }
        )

        self.assertEqual(400, response.status_code)


class VoteOnInvitationViewTestCase(APITestCase):


    def setUp(self):
        self.election = Election.objects.create(
            title="Test election",
            candidates=[
                "Seb",
                "Pierre-Louis",
            ],
            on_invitation_only=True,
        )

        self.token = Token.objects.create(
            election=self.election,
            email="joe@example.com",
        )

    def test_valid_vote(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [0, 0],
                "token": self.token.id
            }
        )

        self.assertEqual(201, response.status_code)


    def test_vote_without_token(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [0, 0],
            }
        )

        self.assertEqual(400, response.status_code)

    def test_vote_wrong_token(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "grades_by_candidate": [0, 0],
                # make sure the token is not the good one
                "token": self.token.id + "#abc"
            }
        )

        self.assertEqual(400, response.status_code)

    def test_vote_already_used_token(self):
        for _ in range(2):
            response = self.client.post(
                urls.vote(),
                {
                    "election": self.election.id,
                    "grades_by_candidate": [0, 0],
                    "token": self.token.id
                }
            )


        self.assertEqual(400, response.status_code)


class VoteWithResutsTestCase(TestCase):

     def setUp(self):

        self.election = Election.objects.create(
            title="Test election",
            candidates=[
                "Seb",
                "Pierre-Louis",
            ],
            on_invitation_only=True,
        )

        self.votes = [
             Vote.objects.create(election=self.election, grades_by_candidate=[1,2]),
             Vote.objects.create(election=self.election, grades_by_candidate=[3, 2]),
             Vote.objects.create(election=self.election, grades_by_candidate=[1,3]),
             Vote.objects.create(election=self.election, grades_by_candidate=[4,1])
        ]


        def test_results_with_majority_judgment(self):
            scores = grades_matrix(e)
            rank = majority_judgment(scores)
            assert rank == [1, 0]
