import argparse
from pathlib import Path
from typing import Optional, Any
import json
from poll_config import ConfigData, read_config
from vote_reader import parse_vote_file, vote_count, vote
from errors import VoteError

# Couldn't find an STD for this
small_additive: float = 0.000000001


def main() -> None:
    parser = argparse.ArgumentParser(
        "Teller", description="A preferential vote counter program."
    )
    parser.add_argument(
        "config_file", type=Path, help="Path to the configuration json file."
    )
    parser.add_argument("vote_file", type=Path, help="Path to the vote csv file.")

    parser.add_argument(
        "--ignore-invalid-votes",
        action="store_true",
        help="If invalid votes should raise an error, or if they should be simply discarded.",
    )

    args = parser.parse_args()

    # Sanity Checking
    config_file: Path = args.config_file
    vote_file: Path = args.vote_file
    assert (
        config_file.is_file()
    ), f"No file found at config file location: {config_file}"
    assert vote_file.is_file(), f"No file found at vote file location: {vote_file}"

    with open(config_file) as fp:
        config = read_config(fp)

    with open(vote_file) as fp:
        votes = parse_vote_file(fp)

    election_results = count_votes(votes, config, args.ignore_invalid_votes)

    print(json.dumps(election_results))


if __name__ == "__main__":
    main()


def count_votes(
    votes: vote_count, config: ConfigData, raise_vote_error: bool
) -> dict[Any, Any]:
    # See ALGORITHM.md to see the logic + algo here
    winners: set[int] = set()
    excluded: set[int] = set()

    # Count total votes
    total_votes: int = 0
    for vote_amounts in votes.values():
        assert type(vote_amounts[0]) == int
        total_votes += vote_amounts[0]

    # Do integer division because while this rounds down,
    # I then add 1 to the result anyway
    # So the quota will always be slightly greater than the fraction
    # Even if it divides cleanly
    quota: int = (total_votes // (config["winner_amount"] + 1)) + 1
    candidate_count: int = len(config["candidates"])
    first_preferences: list[int] = [0] * candidate_count
    # Counting first preferences

    # Prepare a list of invalid votes to remove if needed
    invalid_votes: list[vote] = list()

    # Prepare a list of first preferences,
    # while also filtering out invalid votes
    for vote_preferences, vote_amounts in votes.items():
        skip_vote: bool = False
        pref_num = len(vote_preferences)
        if pref_num == 0:
            # Invalid vote
            if raise_vote_error:
                raise VoteError(f"Empty vote: {vote_preferences}")
            invalid_votes.append(vote_preferences)
            skip_vote = True
        if pref_num > candidate_count:
            if raise_vote_error:
                raise VoteError(
                    f"Vote contains too many preferences: {vote_preferences}"
                )
            invalid_votes.append(vote_preferences)
            skip_vote = True
        if (
            pref_num < config["minimum_preferences"]
            and config["minimum_preferences"] > 0
        ):
            if raise_vote_error:
                raise VoteError(
                    f"Vote doesn't contain enough preferences: {vote_preferences}"
                )
            invalid_votes.append(vote_preferences)
            skip_vote = True

        for vote_index in vote_preferences:
            if vote_index < 0 or vote_index >= candidate_count:
                if raise_vote_error:
                    raise VoteError(
                        f"Vote contains invalid preferences: {vote_preferences}"
                    )
                invalid_votes.append(vote_preferences)
                skip_vote = True

        if not skip_vote:
            # Get the first vote in the preference list
            first: int = vote_preferences[0]
            # Keep type checker happy
            assert type(vote_amounts[0]) == int
            # Increase the first preferences for that party by the number of votes
            # No need to use the multiplier because we aren't at that stage of counting
            first_preferences[first] += vote_amounts[0]

    # Filtering out votes marked invalid
    for to_remove in invalid_votes:
        del votes[to_remove]

    # Done counting first preferences, now to go through and select a winner!
    while len(winners) < config["winner_amount"]:
        current_votes: list[int] = [0] * candidate_count
        for vote_preferences, vote_amounts in votes.items():
            # Find first un-eliminated preference
            for possible_pref in vote_preferences:
                if possible_pref not in excluded:
                    # Found one!
                    # As we're multiplying an int by a float and casting back to int
                    # Add a small number to prevent floating point muckiness
                    current_votes[possible_pref] += int(
                        vote_amounts[0] * vote_amounts[1] + small_additive
                    )
                    break

        # Next, find the most voted for candidate
        max_votes, max_vote_index = minmax_voted_candidate(current_votes, True)

        # Seeing if they win
        if max_votes >= quota:
            # Ding ding ding! We have a winner!
            winners.add(max_vote_index)

            # If there are more winners needed, lets exclude the candidate
            # And add transfer multipliers
            if len(winners) < config["winner_amount"]:
                transfer_value: float = (max_votes - quota) / max_votes
                apply_mult_for_candidate(
                    votes, transfer_value, max_vote_index, excluded
                )

            # Now add the winner to the excluded list for future votes
            excluded.add(max_vote_index)
        else:
            # Nobody won, removing the least voted candidate
            _, min_vote_index = minmax_voted_candidate(current_votes, False)
            excluded.add(min_vote_index)

        # TODO: Check for edge cases
        # (Ties when there shouldn't be one)
        # Current algorithm shouldn't hang as I'm always excluding
        # 1 additional choice with each loop however

    # By this point we have a list of winners
    return {
        "winners": list(winners),
        "tied_winners": [],
        "first_preferences": first_preferences,
    }


def apply_mult_for_candidate(
    votes: vote_count, transfer_mult: float, target_candidate: int, excluded: set[int]
) -> None:
    for vote_preferences, vote_amounts in votes.items():
        # Find first un-eliminated preference
        for possible_pref in vote_preferences:
            if possible_pref == target_candidate:
                # Found one!
                # Multiplying the vote multiplier by the transfer value
                vote_amounts[1] *= transfer_mult
                break
            if possible_pref not in excluded:
                # This vote currently goes to someone else don't worry about it
                break


def minmax_voted_candidate(vote_list: list[int], most: bool) -> tuple[int, int]:
    min_votes: Optional[int] = None
    min_vote_index: Optional[int] = None
    for index, vote_count in enumerate(vote_list):
        if min_votes is None or (
            most and vote_count > min_votes or not most and vote_count < min_votes
        ):
            min_votes = vote_count
            min_vote_index = index

    # Keeping type checker happy
    assert min_votes is not None
    assert min_vote_index is not None
    return min_votes, min_vote_index
