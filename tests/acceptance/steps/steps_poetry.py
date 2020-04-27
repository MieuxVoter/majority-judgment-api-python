"""
These steps should effect nothing.
They help keep the features idiomatic, suggest additions, etc.
"""

from behave import step


@step(u"etc[.]?|…|[.]{2,}")
def et_caetera(context):
    pass


@step(u"ce n'est pas tout *!*:?")
def but_wait_there_is_more(context):
    pass
