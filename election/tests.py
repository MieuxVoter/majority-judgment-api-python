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

