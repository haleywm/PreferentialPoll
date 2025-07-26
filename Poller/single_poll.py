# single_poll.py
# SinglePoll class, which manages stuff for an individual poll
# I figured just calling it Poll would be really confusing
import msgspec
import aiofiles
from aiofiles import os as aos
import os
import sys
import asyncio
from pathlib import Path
from poll_data import PollData, PollResults, PollSummary

TELLER_LOCATION = os.getenv("TELLER_LOCATION", "../Teller/main.py")
MAX_RUNTIME = 60.0
# 1 megabyte in bytes
MAX_VOTE_SIZE = 1048576


class SinglePoll:
    config: PollData
    _current_results: PollResults | None
    config_path: Path
    votes_path: Path
    # Used to prevent simultaneous access of vote files
    _file_lock: asyncio.Lock
    # Use to store pending votes
    _pending_votes: list[list[int]]

    def __init__(self, config: PollData, config_path: Path, votes_path: Path):
        self.config = config
        self.config_path = Path(config_path).absolute()
        self.votes_path = Path(votes_path).absolute()
        self.teller_path = Path(TELLER_LOCATION).absolute()
        self._file_lock = asyncio.Lock()
        self._pending_votes = []
        self._current_results = None

    async def get_results(self, prefer_immediate: bool) -> PollResults:
        if self._current_results is None:
            # Results not yet calculated
            await self._update_results()

        # self._current_results should always not be none by the time update results is run
        assert self._current_results is not None

        if prefer_immediate:
            # Get results immediately
            result = self._current_results
        else:
            # Now wait until results are available
            # (in case results are currently being calculated)
            async with self._file_lock:
                result = self._current_results
        return result

    async def _update_results(self) -> None:
        # Check if there are pending votes,
        # and flush the pending votes to file if needed
        # Then run Teller if needed

        # Check if votes or no votes
        votes_to_write: list[list[int]] = []
        run_teller = True
        if len(self._pending_votes) != 0:
            # Flush list before awaiting to avoid race conditions
            # around later _pending_votes modification
            votes_to_write = self._pending_votes
            self._pending_votes = []
            await self._write_votes(votes_to_write)
        else:
            # No pending votes, check if no other votes
            if self._current_results is None:
                async with self._file_lock:
                    if await aos.path.getsize(self.votes_path) == 0:
                        # If there were no pending votes,
                        # self._current_results is None,
                        # and the votes file is empty,
                        # then set a default full tie
                        # and don't bother running run_teller
                        candidate_count = len(self.config.candidate_names)
                        self._current_results = PollResults(
                            winners=[],
                            tied_winners=list(range(candidate_count)),
                            first_preferences=[0] * candidate_count,
                        )
                        run_teller = False
            else:
                # No new votes and we've already counted votes, do nothing
                run_teller = False

        # Run Teller if needed
        if run_teller:
            # Call Teller and calculate the results of the election
            # given the current config and votes
            async with self._file_lock:
                # Run process
                # sys.executable gives an absolute path to the current python executable
                # And all other paths were converted to absolute for safety
                proc = await asyncio.create_subprocess_exec(
                    sys.executable,
                    self.teller_path,
                    self.config_path,
                    self.votes_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    proc_output, proc_err = await asyncio.wait_for(
                        proc.communicate(), MAX_RUNTIME
                    )
                    if proc.returncode != 0:
                        # Error!
                        print(
                            f"Error! Subprocess returned {proc.returncode}\nStderr: {proc_err.decode()}\nStdout: {proc_output.decode()}"
                        )
                    else:
                        # Everything worked good!
                        self._current_results = msgspec.json.decode(
                            proc_output, type=PollResults
                        )
                except TimeoutError:
                    # The code has run for a solid minute, assume it got stuck and quit
                    proc.kill()
                    print(f"Error! Subprocess hung for {MAX_RUNTIME} seconds")
        # There is no need to check if more votes were added while the program was running
        # Because add_vote will schedule more runs of _update_results for each new vote
        # If _update_results runs with no pending votes (and self._current_results is not None)
        # Then it will quit without doing anything or awaiting anything

    def add_vote(self, vote: list[int]) -> None:
        # Currently not asserting anything, assuming that's done elsewhere
        # Append new vote to the list
        self._pending_votes.append(vote)
        # Schedule a run of self._update_results() when there's time
        asyncio.create_task(self._update_results())

    async def _write_votes(self, votes_to_write: list[list[int]]) -> None:
        async with self._file_lock:
            # If the file is too big then just don't write the vote
            # This would be bad if the code is meant to be used in a big context
            # But eh

            if await aos.path.getsize(self.votes_path) < MAX_VOTE_SIZE:
                # Append the new line to the votes file
                async with aiofiles.open(self.votes_path, "at") as f:
                    for vote in votes_to_write:
                        await f.write(",".join([str(x) for x in vote]) + "\n")
            else:
                print(
                    f"File {self.votes_path} is bigger than the max size of {MAX_VOTE_SIZE} bytes! Dropping votes to prevent abuse"
                )

    def list_json(self) -> PollSummary:
        # Return the relevant data from self to be represented in the poll list
        # Currently just the poll name is used
        return PollSummary(self.config.election_name, self.config.election_id)

    async def write_files(self, force_write: bool = False) -> None:
        # Avoid fighting with other tools trying to write files before this is done
        async with self._file_lock:
            # Create the necessary folders as needed
            # Then create an empty votes file if needed
            # And save the config file to output
            folder_path = self.votes_path.parent
            assert folder_path == self.config_path.parent

            # Make necessary directories but only if needed
            # This should raise an error if folder_path is taken by a file
            await aos.makedirs(folder_path, exist_ok=True)

            # Make empty votes file if needed
            if not await aos.path.exists(self.votes_path):
                # Open file in append mode then immediatly closing seems to the best touch equiv
                async with aiofiles.open(self.votes_path, "a"):
                    pass

            # Save config if needed
            if force_write or not await aos.path.exists(self.config_path):
                async with aiofiles.open(self.config_path, "wb") as f:
                    await f.write(msgspec.json.encode(self.config))

    @classmethod
    def from_file(cls, config_path: Path, votes_path: Path) -> "SinglePoll":
        # TODO: Read config file, figure out msgspec easy way to do it
        # Unable to use file_lock as class not yet created
        # Must assume that no other resources are attempting to use file
        # As the class doesn't exist to write anything yet
        with open(config_path, "rt") as f:
            config = msgspec.json.decode(f.read(), type=PollData)

        return cls(config, config_path, votes_path)
