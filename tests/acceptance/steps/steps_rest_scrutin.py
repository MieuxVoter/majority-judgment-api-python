"""
REST steps about polls.
These steps deal with the REST API, not the database.
"""

from behave import given, when, then, step
from hamcrest import assert_that, equal_to

from toolbox import parse_actor, parse_yaml


###############################################################################


# @when
@step(u"(?P<actor>.+) crée un(?: autre)? scrutin comme suit *:?")
def actor_creates_a_poll_like_so(context, actor):
    data = parse_yaml(context)
    actor = parse_actor(context, actor)
    actor.post('/polls', data={
        'title': data.get('title'),
        'candidates': data.get('candidates'),
        'num_grades': data.get('grades', 7),
    })
