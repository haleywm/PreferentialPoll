# poll_manager.py
# Poll Manager Class which manages various polls
from pathlib import Path
from single_poll import SinglePoll
from poll_data import PollSummary, NewPoll, PollData
from dataclasses import asdict
from asyncio import Lock

DEFAULT_FOLDER = "polls"


class PollManager:
    polls: dict[int, SinglePoll]
    folder: Path
    _manager_lock: Lock

    def __init__(self, folder: str = DEFAULT_FOLDER) -> None:
        self._manager_lock = Lock()
        # Create folder if doesn't exist
        folder_path = Path(folder)
        # This will raise error if path is taken by non folder object
        folder_path.mkdir(exist_ok=True)
        self.folder = folder_path

        self.polls = dict()

        # Check for existing polls
        for child in folder_path.iterdir():
            # Only check children
            if child.is_dir():
                # If folder contains valid files then create sub-poll
                config_path, votes_path = self._get_config_votes_paths(child)
                if config_path.is_file() and votes_path.is_file():
                    new_poll = SinglePoll.from_file(config_path, votes_path)
                    if new_poll.config.election_id in self.polls:
                        print(
                            f"Warning: Multiple polls using ID {new_poll.config.election_id}"
                        )
                    self.polls[new_poll.config.election_id] = new_poll
                else:
                    print(
                        f"Warning: folder {child} is in poll folder but doesn't contain poll files"
                    )
            else:
                print(f"Warning: non poll file {child} is in poll folder")

    async def add_poll(self, new_poll: NewPoll) -> int:
        # As this function gets the next id, and later actuall reserves it
        # Lock this function to only run one at a time
        # To prevent race conditions where multiple add_poll instances get the same id
        async with self._manager_lock:
            new_id = self._get_next_id()
            # Create full_data from new_poll by turning new_poll into a dict
            # And then unpacking that dictionary as parameters to make PollData
            # Adding on the election id at the end
            full_data = PollData(**asdict(new_poll), election_id=new_id)
            # Get paths, make a poll object, and make it write those files
            folder_path = self.folder / str(new_id)
            config_path, votes_path = self._get_config_votes_paths(folder_path)
            poll = SinglePoll(full_data, config_path, votes_path)
            await poll.write_files(True)

            # Finally, add the poll to the list and return this id
            self.polls[new_id] = poll
        return new_id

    def poll_list(self) -> list[PollSummary]:
        result: list[PollSummary] = []
        for poll in self.polls.values():
            result.append(poll.list_json())

        return result

    def _get_next_id(self) -> int:
        return max(self.polls.keys()) + 1

    def _get_config_votes_paths(self, folder_path: Path) -> tuple[Path, Path]:
        return folder_path / "config.json", folder_path / "votes.csv"
