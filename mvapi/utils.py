import numpy as np
from django.db.models import Count
from django.core.exceptions import EmptyResultSet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
import math


def majority_judgment(results):
    ''' Return the ranking from results using the majority judgment '''
    results = [Result(i, r) for i, r in enumerate(results)]
    results = sorted(results, reverse=True)
    return [r.rid for r in results]


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

    print(A, B)
    Ac = np.copy(A)
    Bc = np.copy(B)
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


def sorted_scores(ratings, Ngrades):
    """ Compute the scores of each candidate """
    Nratings = len(ratings)
    grades = range(Ngrades)
    scores = [len(np.where(ratings == g)[0])/Nratings for g in grades]
    return scores


def plot_scores(scores, grades=[], names=[], height = 0.8, color = [], figure=None, output=True):
    """ scores is a 2D np.array """

    if not output:
        import matplotlib
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    Ncandidates, Ngrades = scores.shape
    ind = np.arange(Ncandidates)  # the x-axis locations for the novels
    plots = []
    width_cumulative = np.zeros(Ncandidates)

    if color == []:
        color = [plt.cm.plasma(1-k/Ngrades, 1) for k in range(Ngrades)]

    if figure == None:
        figure = plt.figure()

    # Move the figure to the right
    ax = figure.add_subplot(111)
    pos1 = ax.get_position() # get the original position
    pos2 = [pos1.x0 + 0.1, pos1.y0,  pos1.width - 0.01, pos1.height]
    ax.set_position(pos2)

    # Draw horizontal bar
    for k in range(Ngrades):
        score = scores[:,k]
        p = plt.barh(ind, score, height=height, left=width_cumulative, color=color[k])
        width_cumulative += score
        plots.append(p)

    # Add labels, titles and legend
    plt.xlim((0, 1))
    plt.xlabel('Mentions')
    plt.ylabel('Candidats')
    plt.yticks(ind, names)
    plt.xticks([],[])
    plt.legend([p[0] for p in plots], grades, loc="best")


def get_scores(election):
    """ Compute a 2D array with all the ratings from the candidates """

    scores = get_ratings(election)

    for i in range(len(scores)):
        scores[i] /= sum(scores[i])

    return scores


class Result():
    """ A verbose way for custom comparison """

    def __init__(self, rid, scores):
        self.rid = rid
        self.scores = scores

    def __lt__(self, other):
        return tie_breaking(self.scores, other.scores)

    def __get__(self):
        return self.scores

    def __repr__(self):
        return "%s - [%s]" % (str(self.rid),  \
                ", ".join([str(s) for s in self.scores]))
