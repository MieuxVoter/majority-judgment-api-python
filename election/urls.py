from django.urls import path
from election.views import *
from django.urls import reverse

app_name = 'election'

urlpatterns = [
    path('create/', ElectionCreateAPIView.as_view(), name="create"),
    path('results/', ElectionResultsAPIView.as_view(), name="results"),
    path('details/', ElectionDetailsAPIView.as_view(), name="details"),
]

def new_election():
    return reverse("election:create")

def election_details(election_pk):
    return reverse("election:details")