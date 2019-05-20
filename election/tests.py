from django.test import TestCase
from rest_framework.test import APITestCase
from election.models import Election, NUMBER_OF_MENTIONS
import election.urls as urls

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
                "candidates": candidates
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
                "mentions_by_candidate": [0, 1],
            }
        )

        self.assertEqual(201, response.status_code)

    def test_too_many_mentions(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "mentions_by_candidate": [0, 1, 0],
            }
        )

        self.assertEqual(400, response.status_code)

    def test_too_few_mentions(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "mentions_by_candidate": [1],
            }
        )

        self.assertEqual(400, response.status_code)

    def test_mention_too_high(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "mentions_by_candidate": [0, NUMBER_OF_MENTIONS],
            }
        )

        self.assertEqual(400, response.status_code)

    def test_mention_too_low(self):
        response = self.client.post(
            urls.vote(),
            {
                "election": self.election.id,
                "mentions_by_candidate": [0, -1],
            }
        )

        self.assertEqual(400, response.status_code)
