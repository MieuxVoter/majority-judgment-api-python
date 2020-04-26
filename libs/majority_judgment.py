from typing import List, Tuple, Dict
from dataclasses import dataclass, field
from operator import attrgetter
import math


Grade = int

def votes_to_merit_profiles(
        votes: List[List[Grade]],
        grades: List[Grade]
        ) -> List[Dict[Grade, int]]:
    """
    Convert a list of votes into a matrix containing the number of grades for
    each candidate
    """

    assert len(votes) > 0, "Empty list of votes"

    num_candidates: int = len(votes[0])
    profiles: List[Dict[Grade, int]] = [
        dict.fromkeys(grades, 0) for _ in range(num_candidates)
    ]

    for vote in votes:
        for candidate_i, grade in enumerate(vote):
            profiles[candidate_i][grade] += 1

    return profiles


def majority_grade(scores: List[int]) -> int:
    mid = math.ceil(sum(scores)/2.0)
    acc = 0
    for i, score in enumerate(scores[::-1]):
        acc += score
        if acc >= mid:
            return len(scores) - 1 - i


# Using gauge for a fast algorithm
# However, it creates paradoxical results with a lower number of votes
@dataclass
class MajorityGauge:
    profile: List[int]
    above: float = 0.
    below: float = 0.
    grade: int = 0.
    sign: int = 0
    gauge: float = 0.

    def __post_init__(self):
        self.grade = majority_grade(self.profile)
        total: int = sum(self.profile)
        self.above = sum(self.profile[:self.grade]) / total
        self.below = sum(self.profile[1 + self.grade:]) / total
        self.sign = 1 if self.above > self.below else -1
        self.gauge = max(self.above, self.below)


def sort_by_gauge(gauges: List[MajorityGauge]) -> List[MajorityGauge]:
    by_gauge: List[MajorityGauge] = sorted(gauges, key=attrgetter("gauge"))
    by_sign: List[MajorityGauge] = sorted(by_gauge, key=attrgetter("sign"))
    return sorted(by_sign, key=attrgetter("grade"), reverse=True)


def sort_by_gauge_with_index(gauges: List[MajorityGauge]
        ) -> List[Tuple[int, MajorityGauge]]:
    by_gauge: List[Tuple[int, MajorityGauge]] = sorted(
            enumerate(gauges), key= lambda x: getattr(x[1], "gauge")
    )
    by_sign: List[Tuple[int, MajorityGauge]] = sorted(
        by_gauge, key= lambda x: getattr(x[1], "sign")
    )
    return sorted(
        by_sign, key= lambda x: getattr(x[1], "grade")
    )


# Long way but no ambiguity
def majority_grade_from_votes(votes: List[int]):
    """
    Each vote is a grade.

    >>> majority_grade_from_votes([15, 16, 17, 18])
    16
    >>> majority_grade_from_votes([15, 17, 17, 18])
    17
    >>> majority_grade_from_votes([15, 16, 17, 17, 18])
    17
    """
    votes = sorted(votes, reverse=False)
    return votes[(len(votes) - 1) // 2]


@dataclass
class MajorityValue:
    profile: Dict[Grade, int]
    values: List[int] = field(default_factory=list)
    grade: int = 0

    def __post_init__(self):
        if self.values == []:
            votes = [
                i for grade, num in self.profile.items()
                for i in [grade] * num
            ]
            for _ in range(len(votes)):
                grade: int = majority_grade_from_votes(votes)
                self.values.append(grade)
                votes.remove(grade)
        self.grade = self.values[0]


def sort_by_value_with_index(
        values: List[MajorityValue]
    ) -> List[Tuple[int, MajorityGauge]]:
    return sorted(
        enumerate(values),
        key=lambda x: getattr(x[1], "values"),
        reverse=True
    )

