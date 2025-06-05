from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Election(Base):
    __tablename__ = "elections"

    id = Column(Integer, primary_key=True, index=True)
    ref = Column(String(20), default="", unique=True)
    name = Column(String(255))
    description = Column(String(1024))
    num_voters = Column(Integer, default=0)
    date_created = Column(DateTime, server_default=func.now())
    date_modified = Column(DateTime, onupdate=func.now())
    date_start = Column(DateTime, server_default=func.now())
    date_end = Column(DateTime)
    hide_results = Column(Boolean, default=False)
    restricted = Column(Boolean, default=False)
    force_close = Column(Boolean, default=False)
    auth_for_result = Column(Boolean, default=False)

    grades = relationship("Grade", back_populates="election")
    candidates = relationship("Candidate", back_populates="election")
    votes = relationship("Vote", back_populates="election")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=False)
    description = Column(String(1024), default="")
    image = Column(String(100), default="")
    date_created = Column(DateTime, server_default=func.now())
    date_modified = Column(DateTime, onupdate=func.now())

    election_ref = Column(String(20), ForeignKey("elections.ref"))
    election = relationship("Election", back_populates="candidates")

    votes = relationship("Vote", back_populates="candidate")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    value = Column(Integer)
    date_created = Column(DateTime, server_default=func.now())
    date_modified = Column(DateTime, onupdate=func.now())

    election_ref = Column(String(20), ForeignKey("elections.ref"))
    election = relationship("Election", back_populates="grades")

    votes = relationship("Vote", back_populates="grade")


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    date_created = Column(DateTime, server_default=func.now())
    date_modified = Column(DateTime, onupdate=func.now())
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    candidate = relationship("Candidate", back_populates="votes")

    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=True)
    grade = relationship("Grade", back_populates="votes")

    election_ref = Column(String(20), ForeignKey("elections.ref"))
    election = relationship("Election", back_populates="votes")
