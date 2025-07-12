# single_poll.py
# SinglePoll class, which manages stuff for an individual poll
# I figured just calling it Poll would be really confusing
from pathlib import Path
from poll_data import PollData, PollResults


class SinglePoll:
    config: PollData
    current_results: PollResults
    config_path: Path
    votes_path: Path

    def __init__(self, config: PollData, config_path: Path, votes_path: Path):
        self.config = config
        self.config_path = config_path
        self.votes_path = votes_path

    @classmethod
    def from_file(cls, config_path: Path, votes_path: Path) -> "SinglePoll":
        # TODO: Read config file, figure out msgspec easy way to do it
        raise NotImplementedError()
