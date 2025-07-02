from typing import TextIO

vote = tuple[int, ...]
vote_count = dict[vote, list[int | float]]


def parse_vote_file(fp: TextIO) -> vote_count:
    # Create new count of votes
    counted_votes: vote_count = dict()
    # Iterate over each line
    for line in fp:
        line = line.strip()
        if len(line) != 0:
            # First, we split the line by commas into a list
            # of strings. Then we convert each strings into an int
            # and pack that into a new list.
            # then we turn this list into a tuple
            # (Only tuples can be added to dicts, as they're immutable)
            votes = tuple([int(x) for x in line.split(",")])

            assert len(votes) > 0

            # Get how many votes match this particular vote,
            # Defaulting to 0 if this vote hasn't been seen before
            # Then add 1 and add it to the vote register
            cur_votes = counted_votes.get(votes, [0, 1.0])
            cur_votes[0] += 1

    return counted_votes
