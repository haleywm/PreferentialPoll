# Teller

Teller is a command line vote counting application. Currently not yet started.

## Input Data

The application takes two different files as input. `config.json`, and `votes.csv`. The format for these files is specified in the root directory, as they are used by both Teller and Poller for storing data.

## Output Data

After processing input, if Teller was able to process the votes successfully, a code of 0 will be returned, and data in the following format will have been printed over stdout:

```JSON
{
    # Will either be "success", or "tie", depending on if the correct number of candidates could be found.
    "election_outcome": str,
    # A list of winner indexes, in order of win. Will have length equal to winner_amount
    # Unless a tie occurred, in which case will be at least 1 shorter
    # And only contain unambiguous wins
    # May be empty where a tie occurred and no victor could be declared
    "winners": [
        int,
        ...
    ],
    # Contains all winners indexes who tied for the same position
    "tied_winners": [
        int,
        ...
    ],
    # Contains a list of number pairs. The first number is the index of a party, while the second number is the number of first preferences that the party received.
    "first_preferences": [
        [int, int],
        ...
    ],
    # Contains each step of the election counting process,
    # with each intermediary stage being a list containing "eliminated" or "elected",
    # followed by a list of eliminated/elected IDs
    # Followed by the transfer value for the votes
    # This value will be 1.0 and can be ignored for all stages except "elected"
    # In which case it will contain the transfer value for each person who voted for the candidate
    # And the final stage being "success", "electedwithoutquota", "randomlychosen" or "tie"
    "election_stages": [
        [str, [int, ...], float],
        ...
    ],
    # Contains the total votes for each candidate after each stage of the election
    # With candidates who were eliminated receiving no votes
    # and candidates who won receiving no further votes
    # (Meaning 0 votes after the round that elected them)
    "votes_per_stage": [
        [float, ...],
        ...
    ],
    # What the computed quota for the election was
    "quota": int
}
```

In the case of an error, a non zero value will be returned, and an error message will be printed over stderr. This message will hopefully be formatted in human readable text explaining the error that occurred.
