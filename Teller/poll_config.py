from typing import TypedDict, TextIO
import json


class ConfigData(TypedDict):
    minimum_preferences: int
    winner_amount: int
    candidates: list[list[str]]
    randomise_order: bool


def read_config(fp: TextIO) -> ConfigData:
    result: ConfigData = json.load(fp)
    return result
