import logging

from django.contrib.postgres.fields import ArrayField
from django.db import IntegrityError, models
from django.conf import settings

from libs.django_randomprimary import RandomPrimaryIdModel

logger = logging.getLogger(__name__)

class Election(RandomPrimaryIdModel):

    title = models.CharField("Title", max_length=255)
    candidates = ArrayField(models.CharField("Name", max_length=255))
    on_invitation_only = models.BooleanField(default=False)

    # An opened election is Doodle-like: results are always visible
    is_opened = models.BooleanField(default=True)
    is_finished = models.BooleanField(default=False)
    is_started = models.BooleanField(default=True)
    num_grades = models.PositiveSmallIntegerField("Num. grades", null=False)

    #Language selection (French by default)
    selec_language = models.CharField("Language", max_length=2,default="fr")

    # make sure we don't ask for more grades than allowed in the database
    def save(self, *args, **kwargs):

        if self.num_grades is None:
            raise IntegrityError("Election requires a positive number of grades.")

        if self.title is None or self.title == "":
            raise IntegrityError("Election requires a proper title")

        if self.num_grades > settings.MAX_NUM_GRADES or self.num_grades <= 0:
            raise IntegrityError(
                "Max number of grades is %d. Asked for %d grades"
                % (self.num_grades, settings.MAX_NUM_GRADES)
            )

        if not self.selec_language in settings.LANGUAGE_AVAILABLE:
            string_language =  ', '.join(settings.LANGUAGE_AVAILABLE)
            raise IntegrityError("Election is only available in " + string_language) 

        return super().save(*args, **kwargs)



class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    grades_by_candidate = ArrayField(models.SmallIntegerField("Note"))

    def save(self, *args, **kwargs):

        logging.debug(self.grades_by_candidate, self.election.candidates)

        if len(self.grades_by_candidate) != len(self.election.candidates):
            raise IntegrityError(
                "number of grades (%d) differs from number of candidates (%d)"
                % (len(self.grades_by_candidate), len(self.election.candidates))
            )

        if not all(0 <= mention < self.election.num_grades
            for mention in self.grades_by_candidate
        ):
            raise IntegrityError(
                "grades have to be between 0 and %d"
                %(self.election.num_grades- 1)
            )

        return super().save(*args, **kwargs)


class Token(RandomPrimaryIdModel):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    email = models.EmailField()
    used = models.BooleanField("Used", default=False)
