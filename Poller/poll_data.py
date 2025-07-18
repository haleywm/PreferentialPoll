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


def validate_poll_data(data: NewPoll) -> None:
    # Not validating types
    # as those should be validated by schema whatever
    if data.winner_amount < 1:
        raise ValidationError("Invalid winner amount")

    if len(data.candidate_names) < data.winner_amount:
        raise ValidationError("Less candidates than winners")

    if len(data.candidate_names) != len(data.candidate_descriptions):
        raise ValidationError("Different number of candidate names and descriptions")

    if data.minimum_preferences > len(data.candidate_names):
        raise ValidationError("More preferences are required than are available")
