"""
REST steps about polls.
These steps deal with the REST API, not the database.
"""

from behave import given, when, then, step
from hamcrest import assert_that, equal_to

from toolbox import parse_actor, parse_yaml, parse_grades, find_poll, fail


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
@step(u"(?P<actor>.+) (?:vote|juge les candidats)(?: comme suit)? (?:sur|de) ce scrutin(?: comme suit)? *:?")
def actor_judges_candidates_of_that_poll_like_so(context, actor):
    actor = parse_actor(context, actor)
    data = parse_yaml(context)
    poll = context.that_poll
    grades = parse_grades(context, data, poll)
    actor.post("/judgments", data={
        'election': poll.id,
        'grades_by_candidate': grades,
    })


# @when
@step(u"l[ea] vainqueur(?:[⋅.-]?e)? de ce scrutin devrait être: (?P<candidate>.+)")
def winner_of_that_poll_should_be(context, candidate):
    actor = parse_actor(context, "C0h4N")
    poll = context.that_poll
    # "/results/{poll.id}/"
    response = actor.get(f"/polls/{poll.id}/results")

    data = response.json()
    # data example :
    # [{'name': 'Islande', 'id': 1, 'grade': 5,
    #   'profile': {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 1, '6': 1}},
    #  {'name': 'France', 'id': 0, 'grade': 1,
    #   'profile': {'0': 0, '1': 1, '2': 1, '3': 0, '4': 0, '5': 0, '6': 0}}]
    assert_that(data[0]['name'], equal_to(candidate))
