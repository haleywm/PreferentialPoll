# Preferential Poll

A project by Haley.

The goal of this project is to make a simple system that lets a website run straw-poll style internet polls, but using a proper implementation of preferential voting.

I'm working on this because I was unable to find any other implementations online that I liked. The ones that I could find were highly critical of the preferential voting system, which I disagree with, and had a very limited implementation, which had a short number of maximum parties. I want to make something which lets people host a customizable implementation of preferential voting, with options for partial votes (such as allowing people to give a minimum of 6 preferences rather than ranking all options), or voting for multiple candidates (choosing the top 3 most popular candidates). It would also be nice to show some fun graphics about how the vote was calculated, however I'll likely leave that until after the initial proof of concept is complete.

## Program Structure

The program is structured into two sub-programs, **Poller** and **Teller**.

### Poller

Poller is the front end, which allows people to create new polls, allows them to vote in existing polls, and calls teller to count the votes and produce a result as needed.

### Teller

Teller is a back end application which actually implements the counting of a preferential vote. Teller is a command line application which takes arguments for what to process, and prints the results in json over stdout, to make it easily fit into a front end as required.

## Input Data

Both Poller and Teller use a pair of two files to store data about individual elections, `config.json`, and `votes.csv`. While running, Poller will produce a `Polls` folder in the working directory, and will create a folder for each new poll, which will be used to store each pair of files. `config.json` is a json file specifying the parameters of the vote, while `votes.csv` should be a csv file simply containing a list of votes in order.

I am aware that this is not the best way of doing this, and a better scaling method would be to use an SQL server. However I'm doing this as a fun hobby project that was never intended to be used by more than a dozen people so I get to decide the requirements and what corners to cut to stay fun and easy to make :3. Others are welcome to fork this code and modify it to serve their own needs.

`config.json` format:

```JSON
{
    # The minimum number of preferences a voter must provide
    # A zero, a negative value, or a value greater than or equal to number of candidates
    # requires all candidates to be preferenced
    "minimum_preferences": int,
    # Number of winners of the election
    # Should be at least 1
    "winner_amount": int,
    # A list of candidates, containing their name and description
    "candidates": [
        [candidate_name: str, candidate_description: str],
        ...
    ],
    # If the order of votes should be randomised every time a polling card is displayed
    "randomise_order": bool
}
```

`votes.csv` should be a CSV file, where each line is a list of preferences, formatted as candidate indexes (as listed in the candidates list) in the order preferenced in that vote, i.e.

```CSV
0,1,2,3,4,5
2,3,1,0,4,5
2,3,1,0,2,5
2,5,1,3,0,4
```
