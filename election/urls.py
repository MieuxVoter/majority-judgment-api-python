from django.urls import path
from election.views import *
from django.urls import reverse

app_name = 'election'

urlpatterns = [
    path(r'', ElectionCreateAPIView.as_view(), name="create"),
    path(r'get/<str:pk>/', ElectionDetailsAPIView.as_view(), name="details"),
    path(r'vote/', vote, name="vote"),
]

def new_election():
    return reverse("election:create")

def election_details(election_pk):
    return reverse("election:details", args=(election_pk,))