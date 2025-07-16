# single_poll.py
# SinglePoll class, which manages stuff for an individual poll
# I figured just calling it Poll would be really confusing
import msgspec
import aiofiles
import os
import sys
import asyncio
from pathlib import Path
from poll_data import PollData, PollResults, PollSummary

TELLER_LOCATION = os.getenv("TELLER_LOCATION", "../Teller/main.py")
MAX_RUNTIME = 60.0


class SinglePoll:
    config: PollData
    _current_results: PollResults | None
    config_path: Path
    votes_path: Path
    # Used to prevent simultaneous access of vote files
    _file_lock = asyncio.Lock()

    def __init__(self, config: PollData, config_path: Path, votes_path: Path):
        self.config = config
        self.config_path = Path(config_path).absolute()
        self.votes_path = Path(votes_path).absolute()
        self.teller_path = Path(TELLER_LOCATION).absolute()

    async def get_results(self, prefer_immediate: bool) -> PollResults:
        if self._current_results is None:
            # Results not yet calculated
            await self._update_results()

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

    async def add_vote(self, vote: list[int]) -> None:
        # Currently not asserting anything, assuming that's done elsewhere
        async with self._file_lock:
            # Append the new line to the votes file
            async with aiofiles.open(self.votes_path, "at") as f:
                # I would like to formally apologise for the one liner
                # I'm better than this but it's fun to write
                # Convert the list into a CSV line in the same order
                # That it was given in the argument
                # And add a newline
                await f.write(",".join([str(x) for x in vote]) + "\n")
        # Now re-calculate votes
        await self._update_results()

    def list_json(self) -> PollSummary:
        # Return the relevant data from self to be represented in the poll list
        # Currently just the poll name is used
        return PollSummary(self.config.election_name)

    @classmethod
    def from_file(cls, config_path: Path, votes_path: Path) -> "SinglePoll":
        # TODO: Read config file, figure out msgspec easy way to do it
        # Unable to use file_lock as class not yet created
        # Must assume that no other resources are attempting to use file
        # As the class doesn't exist to write anything yet
        with open(config_path, "rt") as f:
            config = msgspec.json.decode(f.read(), type=PollData)

        return cls(config, config_path, votes_path)
