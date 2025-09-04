import argparse
from pathlib import Path
from typing import Optional, TypeAlias, Mapping, Sequence
import json
import math
import random
from poll_config import ConfigData, read_config
from vote_reader import parse_vote_file, vote_count, vote
from errors import VoteError

# Couldn't find an STD for this
small_additive: float = 0.000000001

JSON: TypeAlias = (
    Mapping[str, "JSON"] | Sequence["JSON"] | str | int | float | bool | None
)


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
        "-i",
        action="store_true",
        help="If invalid votes should raise an error, or if they should be simply discarded.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print additional information before json file.",
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

    election_results = count_votes(
        votes, config, not args.ignore_invalid_votes, args.verbose
    )
    # If in verbose mode print a line of three dashes
    # To indicate end of debug and beginning of output
    if args.verbose:
        print("---")

    print(json.dumps(election_results))


def count_votes(
    votes: vote_count, config: ConfigData, raise_vote_error: bool, verbose: bool
) -> dict[str, JSON]:
    # See ALGORITHM.md to see the logic + algo here
    winners: set[int] = set()
    tied_winners: list[int] = list()
    excluded: set[int] = set()

    assert len(votes) > 0, "No votes!"

    # Count total votes
    total_votes: int = 0
    for vote_amounts in votes.values():
        assert type(vote_amounts[0]) == int
        total_votes += vote_amounts[0]

    # Do integer division because while this rounds down,
    # I then add 1 to the result anyway
    # So the quota will always be slightly greater than the fraction
    # Even if it divides cleanly
    quota: float = (total_votes / (config["winner_amount"] + 1)) + 1
    candidate_count: int = len(config["candidate_names"])
    first_preferences: list[int] = [0] * candidate_count

    # Creating counters for election info for explanation purposes
    election_stages: list[tuple[str, list[int], float]] = list()
    votes_per_stage: list[list[float]] = list()

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

        votes_seen = set()
        for vote_index in vote_preferences:
            if vote_index < 0 or vote_index >= candidate_count:
                if raise_vote_error:
                    raise VoteError(
                        f"Vote contains invalid preferences: {vote_preferences}"
                    )
                invalid_votes.append(vote_preferences)
                skip_vote = True
            if vote_index in votes_seen:
                if raise_vote_error:
                    raise VoteError(
                        f"Vote contains multiple of the same preference: {vote_preferences}"
                    )
                invalid_votes.append(vote_preferences)
                skip_vote = True
            votes_seen.add(vote_index)

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

    if verbose:
        print(f"{votes=}")
        print(f"{quota=}")

    # Done counting first preferences, now to go through and select a winner!
    # Keep going until we have enough winners, or a tie is found
    while len(winners) < config["winner_amount"] and len(tied_winners) == 0:
        current_votes: list[float] = [0.0] * candidate_count
        for vote_preferences, vote_amounts in votes.items():
            # Find first un-eliminated preference
            for possible_pref in vote_preferences:
                if possible_pref not in excluded:
                    # Found one!
                    current_votes[possible_pref] += vote_amounts[0] * vote_amounts[1]
                    break

        # Save the vote count for the detailed info
        # (Don't strictly need to copy currently,
        # but doing it keeps me safe in case I change the algorithm later and forget)
        votes_per_stage.append(current_votes.copy())

        # Next, find the most voted for candidate
        max_votes, max_vote_indexes = max_voted_candidates(current_votes, excluded)

        # Seeing if they win
        if max_votes + small_additive >= quota:
            # Ding ding ding! We have a winner!
            # See how many winners
            if len(max_vote_indexes) + len(winners) <= config["winner_amount"]:
                # A good number of winners!
                winners.update(max_vote_indexes)
                # If there are more winners needed, lets exclude the candidate
                # And add transfer multipliers
                if len(winners) < config["winner_amount"]:
                    transfer_value = (max_votes - quota) / max_votes
                    apply_mult_for_candidate(
                        votes, transfer_value, max_vote_indexes, excluded
                    )

                    # And save this result for this round
                    election_stages.append(
                        ("elected", max_vote_indexes, transfer_value)
                    )
                else:
                    # No more winners needed
                    election_stages.append(("success", max_vote_indexes, 1.0))

                # Now add the winner to the excluded list for future votes
                excluded.update(max_vote_indexes)

                if verbose:
                    print(f"{max_vote_indexes} won with {max_votes} votes!")
            else:
                # Uh oh! Too many winners! This results in a tie
                election_stages.append(("tie", max_vote_indexes, 1.0))
                if verbose:
                    print(f"Too many winners! Declaring a tie with {max_vote_indexes}")
                tied_winners.extend(max_vote_indexes)
        else:
            # Nobody won
            # First: Check if the "Elected without a quota" or
            # "Two Candidates tied for last vacancy" rules can apply
            remaining_candidates = candidate_count - len(excluded)
            winners_needed = config["winner_amount"] - len(winners)

            if remaining_candidates == 2 and winners_needed == 1:
                # Generate a set of the two remainders
                remainders = list(set(range(candidate_count)).difference(excluded))
                remainders_votes = [current_votes[i] for i in remainders]
                winner_index: int
                random_pick = False
                if math.isclose(remainders_votes[0], remainders_votes[1]):
                    # Votes are equal, randomly pick a winner
                    winner_index = random.randint(0, 1)
                    random_pick = True
                    if verbose:
                        print(
                            f"Randomly picked {remainders[winner_index]} with only {remainders_votes[winner_index]} votes, under rule which allows two ties to be resolved by lot."
                        )

                elif remainders_votes[0] > remainders_votes[1]:
                    # 0 has more votes, and wins without meeting quota
                    winner_index = 0
                else:
                    # 1 has more votes, and wins without meeting quota
                    winner_index = 1

                if verbose and not random_pick:
                    print(
                        f"Elected {remainders[winner_index]} with only {remainders_votes[winner_index]} due to elected without a quota rule"
                    )

                winners.add(remainders[winner_index])
                election_stages.append(
                    (
                        "randomlychosen" if random_pick else "electedwithoutquota",
                        [remainders[winner_index]],
                        1.0,
                    )
                )

            elif remaining_candidates == winners_needed:
                # We have the exact number of remaining candidates to fill the needed positions
                # elect them without them meeting quota
                remainders = list(set(range(candidate_count)).difference(excluded))
                if verbose:
                    print(
                        f"Under the elected without quota rule, electing {remainders} without them meeting quota as there are equal remainders to positions needed"
                    )
                winners.update(remainders)
                election_stages.append(("electedwithoutquota", remainders, 1.0))
            else:
                # Special rules don't fit
                # Removing the least voted candidate(s)
                min_votes, min_vote_indexes = min_voted_candidates(
                    current_votes, excluded
                )
                if len(min_vote_indexes) + len(excluded) == candidate_count:
                    # The excluding these candidates would cause there to be no more candidates
                    # This means that we have a tie where no candidate has enough votes to meet quota
                    # Declare these candidates as tied and end
                    if verbose:
                        print(
                            f"Couldn't find any winners! Declaring a tie with {min_vote_indexes}"
                        )
                    tied_winners.extend(min_vote_indexes)
                    election_stages.append(("tie", min_vote_indexes, 1.0))
                else:
                    excluded.update(min_vote_indexes)
                    election_stages.append(("eliminated", min_vote_indexes, 1.0))
                    if verbose:
                        print(
                            f"{min_vote_indexes} have been excluded for only having {min_votes} votes"
                        )

        if verbose:
            print(f"{votes=}")
            print(f"{winners=}")
            print(f"{excluded=}")

    # By this point we have a list of winners
    return {
        "winners": list(winners),
        "tied_winners": tied_winners,
        "first_preferences": first_preferences,
        "election_stages": election_stages,
        "votes_per_stage": votes_per_stage,
        "quota": quota,
    }


def apply_mult_for_candidate(
    votes: vote_count,
    transfer_mult: float,
    target_candidates: list[int],
    excluded: set[int],
) -> None:
    for vote_preferences, vote_amounts in votes.items():
        # Find first un-eliminated preference
        for possible_pref in vote_preferences:
            if possible_pref in target_candidates:
                # Found one!
                # Multiplying the vote multiplier by the transfer value
                vote_amounts[1] *= transfer_mult
                break
            if possible_pref not in excluded:
                # This vote currently goes to someone else don't worry about it
                break


def max_voted_candidates(
    vote_list: list[float], excluded: set[int]
) -> tuple[float, list[int]]:
    max_votes: Optional[float] = None
    max_vote_indexes: list[int] = []
    for index, vote_count in enumerate(vote_list):
        if index not in excluded:
            if max_votes is None or vote_count > max_votes:
                max_votes = vote_count
                max_vote_indexes = [index]
            elif vote_count == max_votes:
                max_vote_indexes.append(index)

    # Keeping type checker happy
    assert max_votes is not None
    return max_votes, max_vote_indexes


def min_voted_candidates(
    vote_list: list[float], excluded: set[int]
) -> tuple[float, list[int]]:
    min_votes: Optional[float] = None
    min_vote_indexes: list[int] = []
    for index, vote_count in enumerate(vote_list):
        if index not in excluded:
            if min_votes is None or vote_count < min_votes:
                min_votes = vote_count
                min_vote_indexes = [index]
            elif vote_count == min_votes:
                min_vote_indexes.append(index)

    # Keeping type checker happy
    assert min_votes is not None
    return min_votes, min_vote_indexes


if __name__ == "__main__":
    main()
