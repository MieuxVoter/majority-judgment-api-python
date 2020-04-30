"""
Local database abstraction layer for step defs.
"""


from django.contrib.auth.models import User
from election.models import Election


def make_user(context, username):
    return User.objects.create_user(
        username=username,
        email='user@test.mieuxvoter.fr',
        password=username
    )


def count_users():
    return User.objects.count()


def count_polls():  # TBD: "scrutin" translates to "poll"?
    return Election.objects.count()


def find_user(identifier, relax=False):
    user = User.objects.get(username=identifier)
    if user is not None:
        return user
    if not relax:
        raise ValueError("No user found matching `%s`." % identifier)
    return None


def find_poll(identifier, relax=False):
    poll = Election.objects.get(title=identifier)
    if poll is not None:
        return poll
    if not relax:
        raise ValueError("No poll found matching `%s`." % identifier)
    return None


