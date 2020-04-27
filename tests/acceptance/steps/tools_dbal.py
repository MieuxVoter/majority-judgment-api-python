"""
Local database abstraction layer for step defs.
"""


from django.contrib.auth.models import User
from election.models import Election


def count_users():
    return User.objects.count()


def count_polls():  # TBD: "scrutin" translates to "poll"?
    return Election.objects.count()


