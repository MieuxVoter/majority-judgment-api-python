"""
REST steps about polls.
These steps deal with the REST API, not the database.
"""

from behave import given, when, then, step
from hamcrest import assert_that, equal_to

from tools_nlp import parse_amount, parse_yaml
from tools_dbal import count_polls


###############################################################################


# @given
@step(u"(?P<actor>.+) crée un(?: autre)? scrutin comme suit *:?")
def actor_creates_a_poll_like_so(context, actor):
    data = parse_yaml(context)

    # How about this instead?
    # actor = parse_actor(context, actor)
    # actor.post('/polls', data={
    #     'title': data.get('title'),
    #     'candidates': data.get('candidates'),
    #     'num_grades': data.get('grades', 7),
    # })

    from django.test import Client
    response = Client().post('/api/election/polls', {
        'title': data.get('title'),
        'candidates': data.get('candidates'),
        'num_grades': data.get('grades', 7),
    })

    print(response.status_code)
    print(response.content)

