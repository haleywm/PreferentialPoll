# poll_manager.py
# Poll Manager Class which manages various polls
from pathlib import Path
from single_poll import SinglePoll

DEFAULT_FOLDER = "polls"


class PollManager:
    polls: dict[int, SinglePoll]

    def __init__(self, folder: str = DEFAULT_FOLDER) -> None:
        # Create folder if doesn't exist
        folder_path = Path(folder)
        # This will raise error if path is taken by non folder object
        folder_path.mkdir(exist_ok=True)

        self.polls = dict()

        # Check for existing polls
        for child in folder_path.iterdir():
            # Only check children
            if child.is_dir():
                # If folder contains valid files then create sub-poll
                config_path = child / "config.json"
                votes_path = child / "votes.csv"
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

    def poll_list(self) -> list[dict[str, str]]:
        result = []
        for poll in self.polls.values():
            result.append(poll.list_json())

        return result
