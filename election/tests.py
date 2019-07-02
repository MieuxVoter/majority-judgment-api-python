import logging
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APITestCase

import election.urls as urls
from election.models import MAX_NUM_GRADES, Election, Token, Vote
from libs.majority_judgment import majority_judgment, votes_to_scores


# To avoid undesirable logging messages due to 400 Error.
logger = logging.getLogger("django.request")
logger.setLevel(logging.ERROR)

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
                "num_grades": 5
            },
        )
        self.assertEqual(201, response_post.status_code)

        election_pk = response_post.data["id"]
        response_get = self.client.get(urls.election_details(election_pk))
        self.assertEqual(200, response_get.status_code)
        self.assertEqual(title, response_get.data["title"])
        self.assertEqual(candidates, response_get.data["candidates"])

    def test_mandatory_fields(self):
        
        # Missing num_grades
        self.assertRaises(IntegrityError, Election.objects.create, 
                 candidates=["Seb", "PL"], title="My election")
        
        # Missing candidates
        self.assertRaises(IntegrityError, Election.objects.create, 
                 num_grades=5, title="My election")
        
        # Missing title
        self.assertRaises(IntegrityError, Election.objects.create, 
                 candidates=["Seb", "PL"], num_grades=5)





class VoteOnInvitationViewTestCase(APITestCase):


    def setUp(self):
        self.election = Election.objects.create(
            title="Test election",
            candidates=[
                "Seb",
                "Pierre-Louis",
            ],
            on_invitation_only=True,
            num_grades=5
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
            num_grades=5,
            on_invitation_only=True,
        )

        self.votes = [
             Vote.objects.create(election=self.election, grades_by_candidate=[1,2]),
             Vote.objects.create(election=self.election, grades_by_candidate=[3, 2]),
             Vote.objects.create(election=self.election, grades_by_candidate=[1,3]),
             Vote.objects.create(election=self.election, grades_by_candidate=[4,1])
        ]


    def test_results_with_majority_judgment(self):
         scores = votes_to_scores([v.grades_by_candidate for v in self.votes], 
                 self.election.num_grades)
         sorted_indexes = majority_judgment(scores)
         assert sorted_indexes == [1, 0]

    def test_num_grades(self):
         self.assertRaises(IntegrityError, Vote.objects.create,
                 election=self.election, grades_by_candidate=[1,6])


    def test_view_existing_election(self):
        response = self.client.get(
            urls.results(self.election.id)
        )
        self.assertEqual(200, response.status_code)


