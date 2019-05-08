from django.test import TestCase
from rest_framework.test import APITestCase
from election.models import Election
from django.urls import reverse
# Create your tests here.

class ElectionCreateAPIViewTestCase(APITestCase):
    url = reverse("election:create")

    def test_create_election(self):
        response = self.client.post(self.url, {"title": "testing election/create !"})
        self.assertEqual(201, response.status_code)

class ElectionResultsAPIViewTestCase(APITestCase):
    url = reverse("election:results")

    def test_election_results(self):
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual("results", response.data["data"])

class ElectionDetailsAPIViewTestCase(APITestCase):
    url = reverse("election:details")

    def test_election_results(self):
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual("details", response.data["data"])        
