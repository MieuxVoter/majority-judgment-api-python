"""
These steps should [ae]ffect nothing.
They help keep the features idiomatic, engaging, etc.
"""

from behave import step
from tools_dbal import find_user


@step(u"j(?:e |')(?:débogue|affiche)(?: l[ea])? citoyen(?:[⋅.-]?ne|)(?: nommé(?:[⋅.-]?e|))? (?P<name>.+)")
@step(u"I print(?: the)? user(?: named)? (?P<name>.+)")
def print_user(context, name):
    user = find_user(name)
    print(user)
