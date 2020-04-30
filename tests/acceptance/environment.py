"""
Environment module for acceptance testing of the scenaristic constitution.
https://behave.readthedocs.io/en/latest/api.html#environment-file-functions
"""
from behave.log_capture import capture

from steps.context_main import reset_context as reset_main_context


# Since we expect most of our step defs to require the flexibility of regular
# expressions (I18N, epicene) we make regular expressions the default.
# This is at the expense of automatic type casting of step variables.
from behave import use_step_matcher

from steps.tools_i18n import guess_language

use_step_matcher("re")
# You can still override this right before your step def if you want,
# by calling use_step_matcher() with one of the following:
# "parse" (factory default), "cfparse"
# and calling it again with "re" after your step def.  (it uses a `global`)


def before_all(context):
    """
    Ran before the whole shooting match.
    """
    pass


def before_feature(context, feature):
    """
    Ran before _each_ feature file is exercised.
    """
    locale = guess_language(context)
    # REQUIRES CUSTOM FORK OF HAMCREST
    from hamcrest import set_locale
    set_locale(locale)
    ##################################


def before_scenario(context, scenario):
    """
    Ran before _each_ scenario is run.
    """
    reset_main_context(context)
    pass


def after_scenario(context, scenario):
    """
    Ran after _each_ scenario is run.
    """
    pass


def after_step(context, step):
    """
    Ran after _each_ step is run.
    """
    pass


def django_ready(context):
    context.django = True
