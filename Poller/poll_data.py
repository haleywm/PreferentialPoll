from dataclasses import dataclass


class ValidationError(Exception):
    pass


# This is data that the client can send
@dataclass
class NewPoll:
    election_name: str
    minimum_preferences: int
    winner_amount: int
    candidate_names: list[str]
    candidate_descriptions: list[str]
    randomise_order: bool


# PollData is the actually stored data class,
# and just needs an added server decided election id
@dataclass
class PollData(NewPoll):
    election_id: int


@dataclass
class PollResults:
    winners: list[int]
    tied_winners: list[int]
    first_preferences: list[int]


@dataclass
class PollSummary:
    election_name: str
    election_id: int


@dataclass
class PollCreationInfo:
    election_id: int


@dataclass
class Vote:
    election_id: int
    preferences: list[int]
