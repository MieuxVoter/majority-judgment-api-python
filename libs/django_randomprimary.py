"""
A new base class for Django models, which provides them with a better and random
looking primary key for the 'id' field.
This solves the problem of having predictable, sequentially numbered primary keys
for Django models.
Just use 'RandomPrimaryIdModel' as base class for your Django models. That's all.
The generated keys are base64-strings.

Inspired from : https://github.com/jbrendel/django-randomprimary/blob/master/random_primary.py
(c) 2012 Juergen Brendel (http://brendel.com/consulting)

"""

import os
import base64
import math
from django.db.utils import IntegrityError
from django.db       import models, transaction
from django.db       import transaction



# This is the bytes-length of randomness. Has to be a multiple of 3 for the
# base64 enconding doesn't padd with "="s.
NUMBER_OF_BYTES = 3 * 5

class RandomPrimaryIdModel(models.Model):

    """ Our new ID field """
    id = models.CharField(
        db_index    = True,
        primary_key = True,
        max_length  = math.ceil(NUMBER_OF_BYTES * 4 / 3),
    )

    def __init__(self, *args, **kwargs):
        """
        Nothing to do but to call the super class' __init__ method and initialize a few vars.
        """
        super(RandomPrimaryIdModel, self).__init__(*args, **kwargs)

    def _make_random_key(self):
        return base64.urlsafe_b64encode(os.urandom(NUMBER_OF_BYTES)).decode()

    def save(self, *args, **kwargs):
        """
        Modified save() function, which selects a special unique ID if necessary.
        Calls the save() method of the first model.Models base class it can find
        in the base-class list.
        """
        if self.id:
            # Apparently, we know our ID already, so we don't have to
            # do anything special here.
            super(RandomPrimaryIdModel, self).save(*args, **kwargs)
            return

        while True:
            # Randomly choose a new unique key
            _id = self._make_random_key()
            sid = transaction.savepoint()       # Needed for Postgres, doesn't harm the others
            try:
                if kwargs is None:
                    kwargs = dict()
                kwargs['force_insert'] = True           # If force_insert is already present in
                                                        # kwargs, we want to make sure it's
                                                        # overwritten. Also, by putting it here
                                                        # we can be sure we don't accidentally
                                                        # specify it twice.
                self.id = _id
                super(RandomPrimaryIdModel, self).save(*args, **kwargs)
                break                                   # This was a success, so we are done here

            except IntegrityError as e:                   # Apparently, this key is already in use
                # Only way to differentiate between different IntegrityErrors is to look
                # into the message string. Too bad. But I need to make sure I only catch
                # the ones for the 'id' column.
                #
                # Sadly, error messages from different databases look different and Django does
                # not normalize them. So I need to run more than one test. One of these days, I
                # could probably just examine the database settings, figure out which DB we use
                # and then do just a single correct test.
                #
                # Just to complicates things a bit, the actual error message is not always in
                # e.message, but may be in the args of the exception. The args list can vary
                # in length, but so far it seems that the message is always the last one in
                # the args list. So, that's where I get the message string from. Then I do my
                # DB specific tests on the message string.
                #
                msg = e.args[-1]
                if msg.endswith("for key 'PRIMARY'") or msg == "column id is not unique" or \
                        "Key (id)=" in msg:
                    transaction.savepoint_rollback(sid) # Needs to be done for Postgres, since
                                                        # otherwise the whole transaction is
                                                        # cancelled, if this is part of a larger
                                                        # transaction.

                else:
                    # Some other IntegrityError? Need to re-raise it...
                    raise e



    class Meta:
        abstract = True