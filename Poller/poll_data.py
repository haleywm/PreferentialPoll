from dataclasses import dataclass


class ValidationError(Exception):
    pass


@dataclass
class PollData:
    election_id: int
    election_name: str
    minimum_preferences: int
    winner_amount: int
    candidate_names: list[str]
    candidate_descriptions: list[str]
    randomise_order: bool


@dataclass
class PollResults:
    winners: list[int]
    tied_winners: list[int]
    first_preferences: list[int]


@dataclass
class PollSummary:
    election_name: str
    election_id: int


def validate_poll_data(data: PollData) -> None:
    # Not validating types
    # as those should be validated by schema whatever
    if data.winner_amount < 1:
        raise ValidationError("Invalid winner amount")

    if len(data.candidate_names) < data.winner_amount:
        raise ValidationError("Less candidates than winners")

    if len(data.candidate_names) != len(data.candidate_descriptions):
        raise ValidationError("Different number of candidate names and descriptions")
