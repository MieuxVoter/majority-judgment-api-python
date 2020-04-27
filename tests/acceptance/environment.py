"""
Environment module for acceptance testing of the scenaristic constitution.
https://behave.readthedocs.io/en/latest/api.html#environment-file-functions
"""


# Since we expect most of our step defs to require the flexibity of regexes,
# we make regular expressions the default.  (I18N, epicene)
# This is at the expense of automatic type casting of step variables.
# It's a somewhat good tradeoff since natural language numbers still do require
# explicit casting in all matchers (AFAIK in early 2020).
from behave import use_step_matcher
use_step_matcher("re")
# You can still override this right before your step def if you want,
# by calling use_step_matcher() with one of the following:
# "parse" (factory default), "cfparse"
# and calling it again with "re" after your step def. (it uses a `global`)


# def _log(*args):
#     print(*args)  # hook to logger instead


def before_feature(context, feature):
    """
    Ran before _each_ feature file is exercised.
    """
    # _log("Before feature", feature)
    pass
    # context.fixtures = ['behave-fixtures.json']


def before_scenario(context, scenario):
    """
    Ran before _each_ scenario is run.
    """
    # _log("Before scenario", scenario)
    pass
    # context.fixtures.append('behave-second-fixture.json')


def before_all(context):
    """
    Ran before the whole shooting match.
    """
    pass


def django_ready(context):
    # _log("Django Ready", context)
    context.django = True
