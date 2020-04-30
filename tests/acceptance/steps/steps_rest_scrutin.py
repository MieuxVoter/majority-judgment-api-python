"""
REST steps about polls.
These steps deal with the REST API, not the database.
"""

from behave import given, when, then, step
from hamcrest import assert_that, equal_to

from toolbox import parse_actor, parse_yaml, parse_grades, find_poll


###############################################################################


# @when
@step(u"(?P<actor>.+) crée un(?: autre)? scrutin comme suit *:?")
def actor_creates_a_poll_like_so(context, actor):
    data = parse_yaml(context)
    actor = parse_actor(context, actor)
    title = data.get('title')
    actor.post('/polls', data={
        'title': title,
        'candidates': data.get('candidates'),
        'num_grades': data.get('grades', 7),
    })
    created_poll = find_poll(title, relax=True)
    if created_poll:
        context.that_poll = created_poll


# @when
@step(u"(?P<actor>.+) vote comme suit sur ce scrutin *:?")
def actor_votes_on_that_poll_like_so(context, actor):
    actor = parse_actor(context, actor)
    data = parse_yaml(context)
    poll = context.that_poll
    grades = parse_grades(context, data, poll)
    actor.post("/votes", data={
        'election': poll.id,
        'grades_by_candidate': grades,
    })
