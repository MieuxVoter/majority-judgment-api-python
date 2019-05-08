from django.urls import path
from election.views import ElectionCreateAPIView

app_name = 'election'

urlpatterns = [
    path('create/', ElectionCreateAPIView.as_view(), name="create"),
]
