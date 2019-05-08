from django.urls import path
from election.views import *

app_name = 'election'

urlpatterns = [
    path('create/', ElectionCreateAPIView.as_view(), name="create"),
    path('results/', ElectionResultsAPIView.as_view(), name="results"),
    path('details/', ElectionDetailsAPIView.as_view(), name="details"),
]
