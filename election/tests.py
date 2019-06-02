from django.test import TestCase
from majority_judgment.tools import get_ranking, get_ratings, majority_grade


class MajorityJudgmentTestCase(TestCase):
    fixtures = ['election.json']

    # def setUp(self):

    def test_ranking(self):
        election_id = 2
        ranking = get_ranking(election_id)
        ranking = [candidate.pk for candidate in ranking]
        ground_truth = [ 2,  3,  4, 13,  6,  7, 15, 14,  8, 12, 16,  5, 11, 17, 10,  1,  9]

        self.assertEqual(ranking, ground_truth)

    def test_majority_grade(self):
        election_id = 2
        ranking = get_ranking(election_id)
        # ratings = get_ratings(election_id)
        majority_grades = [majority_grade(candidate.ratings) for candidate in ranking]
        ground_truth = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        
        self.assertEqual(majority_grades, ground_truth)
