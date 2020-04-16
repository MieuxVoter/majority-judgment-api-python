from typing import List
import math


def majority_grade(scores: List[int]) -> int:
    mid = math.ceil(sum(scores)/2.0)
    acc = 0
    for i, score in enumerate(scores[::-1]):
        acc += score
        if acc >= mid:
            return len(scores) - 1 - i


def majority_score(x: List[int], grade: int) -> float:
    total = sum(x)
    left = sum(x[:grade])
    right = sum(x[:1 + grade])
    return -left/total if left > right else right/total


def tie_breaking(a: List[int], b: List[int]):
    ''' algorithm to divide out candidates with the same median grade.
    Return True if a < b (or if b has a better ranking than a)'''
    med_a = majority_grade(a)
    med_b = majority_grade(b)

    while med_a == med_b:

        a[med_a] -= 1
        b[med_b] -= 1

        if a[med_a] < 0:
            return True
        if b[med_b] < 0:
            return False

        med_a = majority_grade(a)
        med_b = majority_grade(b)

    return med_a < med_b



class VotesByCandidate():
    """ A verbose way for custom comparison """

    def __init__(self, id, profile):
        self.id = id
        self.profile = profile

    def __lt__(self, other: "VotesByCandidate") -> bool:
        return tie_breaking(self.profile.copy(), other.profile.copy())

    def __get__(self) -> List[int]:
        return self.profile

    def __repr__(self):
        return "%s - [%s]" % (str(self.id),
                ", ".join([str(s) for s in self.profile]))


def compute_votes(votes: List[List[int]], num_grades: int):

    pref_profiles = votes_to_pref_profiles(votes, num_grades)
    scores = []
    grades = []
    ranking = []

    for profile in pref_profiles:
        grade = majority_grade(profile)
        score = majority_score(profile, grade)

        scores.append(score)
        grades.append(grade)

    num_candidates = len(pref_profiles)
    tuples = [(num_grades - g, s) for g, s in zip(grades, scores)]
    ranking = sorted(range(num_candidates), reverse=True, key=tuples.__getitem__)
    
    return pref_profiles, scores, grades, ranking


def votes_to_pref_profiles(votes: List[List[int]], num_grades: int):
    """
    Convert a list of votes into a matrix containing the number of grades for
    each candidate
    """

    assert len(votes) > 0, "Empty list of votes"

    grades = [0] * num_grades
    num_candidates = len(votes[0])
    profiles = [grades.copy() for _ in range(num_candidates)]

    for vote in votes:
        for i, grade in enumerate(vote):
            profiles[i][grade] += 1

    return profiles


def majority_judgment(pref_profiles: List[List[int]]) -> List[int]:
    '''
    Return the id of each candidate ranked wrt. their preference profiles.

    A preference profile contains the number of votes for each grade.
    '''
    results: List[VotesByCandidate] = [
            VotesByCandidate(i, r) for i, r in enumerate(pref_profiles)
    ]
    results = sorted(results, reverse=True)
    return [r.id for r in results]
