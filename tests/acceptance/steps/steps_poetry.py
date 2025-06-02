"""
These steps should [ae]ffect nothing.
They help keep the features idiomatic, engaging, etc.
"""

from behave import step


@step(u"(?:etc[.]?|…|[.]{3,}|[?!]+)[?!]*")
def et_caetera(context):
    pass  # nothing is cool


@step(u"ce n'est pas tout *!*:?")
def wait_there_is_more(context):
    pass  # nothing is cool
