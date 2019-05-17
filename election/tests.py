from django.test import TestCase
from rest_framework.test import APITestCase
from election.models import Election
import election.urls as urls


class ElectionCreateAPIViewTestCase(APITestCase):

    def test_create_election(self):
        response_post = self.client.post(
            urls.new_election(),
            {"title": "testing election/create !"},
        )
        self.assertEqual(201, response_post.status_code)


class ElectionDetailsAPIViewTestCase(APITestCase):

    def test_election_results(self):
        response = self.client.get(urls.election_details(None))
        self.assertEqual(200, response.status_code)
        self.assertEqual("details", response.data["data"])
