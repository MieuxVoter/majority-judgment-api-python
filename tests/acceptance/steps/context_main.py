"""
What we need:
- Share context between step defs (including from different files)
- Easy and scalable context reset on each scenario
- Multiple contexts (do we?)

Context variables in themselves must be as scarce as possible,
and only added after careful consideration, though.

So far we're using the PatchedContext instance provided by behave.
"""


def reset_context(context):
    context.that_user = None
    context.that_poll = None
