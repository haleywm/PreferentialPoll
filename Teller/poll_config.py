from typing import TypedDict, TextIO
import json


class ConfigData(TypedDict):
    election_name: str
    minimum_preferences: int
    winner_amount: int
    # This would be a list[tuple[str, str]]
    # But json doesn't do tuples
    # This program only cares about the length of the top list
    # And not the contents of the strings anyway so it's fine
    candidate_names: list[str]
    candidate_descriptions: list[str]
    randomise_order: bool


def read_config(fp: TextIO) -> ConfigData:
    result: ConfigData = json.load(fp)
    return result
