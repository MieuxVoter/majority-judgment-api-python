"""
These steps should effect nothing.
They help keep the features idiomatic, suggest additions, etc.
"""

from behave import step


@step(u"etc[.]?|…|[.]{2,}")
def et_caetera(context):
    pass

