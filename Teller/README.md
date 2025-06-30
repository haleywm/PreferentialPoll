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
    ]
}
```

In the case of an error, a non zero value will be returned, and an error message will be printed over stderr. This message will hopefully be formatted in human readable text explaining the error that occurred.
