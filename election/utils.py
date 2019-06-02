import numpy as np
from django.db.models import Count
from django.core.exceptions import EmptyResultSet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
import math

from mvapi.utils import majority_judgment
from election.models import Election, Vote


def grades_matrix(election):
    """ Compute a 2D array with the sum of each grade given for each candidate """ 

    votes = Vote.objects.filter(election=election)

    num_grades = election.num_grades
    num_candidates = len(election.candidates)
    scores = np.zeros((num_candidates, num_grades), dtype=int)

    for vote in votes:
        for i, grade in enumerate(vote.grades_by_candidate):
            scores[i, grade] += 1

    return scores


def get_ranking(election_id):

    election = get_object_or_404(Election, pk=election_id)
    candidates = election.candidates

    # fetch results
    ratings = get_ratings(election)
    results = []
    Nvotes = len(Rating.objects.filter(election=election))

    if Nvotes == 0:
        raise EmptyResultSet(_("No vote has already been casted."))

    for i, candidate in enumerate(candidates):
        result = Result(candidate=candidate,
                        ratings=ratings[i, :],
                        grades=grades)
        results.append(result)

    # ranking according to the majority judgment
    ranking = []

    for r in majority_judgment(results):

        candidate = r.candidate
        candidate.ratings = r.ratings
        candidate.majority_grade = grades[majority_grade(r.ratings)]
        ranking.append(candidate)

    return ranking
