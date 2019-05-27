from django.db import models, IntegrityError
from django.contrib.postgres.fields import ArrayField
from libs.django_randomprimary import RandomPrimaryIdModel


NUMBER_OF_MENTIONS = 7

class Election(RandomPrimaryIdModel):
    title = models.CharField("Title", max_length=255)
    candidates = ArrayField(models.CharField("Name", max_length=255))
    on_invitation_only =models.BooleanField(default=False)


class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    mentions_by_candidate = ArrayField(models.SmallIntegerField("Note"))

    def save(self, *args, **kwargs):
        print(self.mentions_by_candidate, self.election.candidates)
        if len(self.mentions_by_candidate) != len(self.election.candidates):
            raise IntegrityError(
                "number of mentions (%d) differs from number of candidates (%d)"
                % (len(self.mentions_by_candidate), len(self.election.candidates))
            )

        if not all(0 <= mention < NUMBER_OF_MENTIONS
            for mention in self.mentions_by_candidate
        ):
            raise IntegrityError(
                "mentions have to be between 0 and %d"
                %(NUMBER_OF_MENTIONS - 1)
            )

        return super().save(*args, **kwargs)

class Token(RandomPrimaryIdModel):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    email = models.EmailField()
    used = models.BooleanField("Used", default=False)
