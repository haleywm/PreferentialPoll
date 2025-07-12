# poll_manager.py
# Poll Manager Class which manages various polls
from pathlib import Path
from single_poll import SinglePoll

DEFAULT_FOLDER = "polls"


class PollManager:
    polls: list[SinglePoll]

    def __init__(self, folder=DEFAULT_FOLDER):
        # Create folder if doesn't exist
        folder_path = Path(folder)
        # This will raise error if path is taken by non folder object
        folder_path.mkdir(exist_ok=True)

        self.polls = list()

        # Check for existing polls
        for child in folder_path.iterdir():
            # Only check children
            if child.is_dir():
                # If folder contains valid files then create sub-poll
                config_path = child / "config.json"
                votes_path = child / "votes.csv"
                if config_path.is_file() and votes_path.is_file():
                    self.polls.append(SinglePoll.from_file(config_path, votes_path))
                else:
                    print(
                        f"Warning: folder {child} is in poll folder but doesn't contain poll files"
                    )
            else:
                print(f"Warning: non poll file {child} is in poll folder")
