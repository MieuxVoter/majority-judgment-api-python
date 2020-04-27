###############################################################################
# Is PyCharm > 2017.3 understanding these for you?
# from behave import given, when, then
# 2017.3 won't, and it's all I got.
# Meanwhile, let's use `step' for the sprint.
from behave import step
# FIXME: swap to usage of `given`, `when`, `then` when relevant
###############################################################################

# Alternatives: move this to __init__.py ?
# from behave import use_step_matcher
# use_step_matcher("re")
# Aliases?
# ⋅e = (?:[⋅.-]?e|)
# ⋅ne = (?:[⋅.-]?ne|)


#

# @given
@step(u"un(?:[⋅.-]?e|) citoyen(?:[⋅.-]?ne|) nommé(?:[⋅.-]?e|) (?P<name>.+)")
def create_citizen_named(context, name):
    print("Creating citizen named `%s'…" % name)
    raise NotImplementedError()

