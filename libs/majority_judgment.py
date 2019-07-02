import math


def majority_grade(x):
    mid = math.ceil(sum(x)/2.0)
    acc = 0
    for i, xi in enumerate(x[::-1]):
        acc += xi
        if acc >= mid:
            return len(x) - 1 - i


def tie_breaking(A, B):
    ''' Algorithm to divide out candidates with the same median grade.
    Return True if A < B (or if B has a better ranking than A)'''

    # lists are mutable
    Ac = A.copy()
    Bc = B.copy()

    medA = majority_grade(Ac)
    medB = majority_grade(Bc)

    while medA == medB:

        Ac[medA] -= 1
        Bc[medB] -= 1

        if Ac[medA] < 0:
            return True
        if Bc[medB] < 0:
            return False

        medA = majority_grade(Ac)
        medB = majority_grade(Bc)

    return medA > medB



class VotesByCandidate():
    """ A verbose way for custom comparison """

    def __init__(self, rid, scores):
        self.rid = rid
        self.scores = scores

    def __lt__(self, other):
        return tie_breaking(self.scores, other.scores)

    def __get__(self):
        return self.scores

    def __repr__(self):
        return "%s - [%s]" % (str(self.rid),  
                ", ".join([str(s) for s in self.scores]))


def votes_to_scores(votes, num_grades):
    """ Convert a list of votes into a matrix containing the number of grades for each candidate """

    assert len(votes) > 0, "Empty list of votes"

    grades = [0] * num_grades
    scores = [grades.copy() for _ in range(len(votes[0]))]

    for vote in votes:
        for i, grade in enumerate(vote):
            scores[i][grade] += 1

    return scores


def majority_judgment(scores):
    ''' 
    Return the ranking from results using the majority judgment 
    
    scores is a 2D list  #candidates x #grades.
    It contains the number of votes given to a candidate for each grade.
    '''
    results = [VotesByCandidate(i, r) for i, r in enumerate(scores)]
    results = sorted(results, reverse=True)
    return [r.rid for r in results]



