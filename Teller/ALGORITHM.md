# Algorithm Planning

Goals:
- A website which allows someone to create a preferential voting poll
- Should allow a user to create a new poll, and share a link to this poll to allow others to vote (Will not worry about preventing voter fraud for initial version since this is a proof of concept)
- Should allow:
	- An unlimited number of candidates (maybe cut off at like 512 if I'm worried about abuse)
	- Unlimited number of responses
	- Optionally allow voters to partially vote after a limit (i.e. vote for the top 6, and allow your vote to be exhausted if your options are eliminated)
	- Optionally allow for multiple winners (i.e. the top 6 candidates win, like how voting in the upper house works).
	- A break down of who was eliminated, and how the votes looked after each elimination would be fun
	- Data exporting and importing would be nice so that I could run this with data from the real elections as a proof of concept
	- Optionally shuffle candidates once, or shuffle for every single voter
- Out of scope:
	- Preventing voter fraud (i.e. with accounts, ip limits, other suspicious behaviour monitoring or captchas)
	- Parties/Group ticket voting
	- The concept of a voter roll, tracking names of voters, the concept of putting your name down as voted but deliberately making an informal vote, anything else informal vote related

## My understanding of preferential voting

Thanks to https://www.aec.gov.au/learn/files/poster-count-senate-pref-voting.pdf and https://www.aec.gov.au/learn/files/poster-counting-hor-pref-voting.pdf for clarifying most edge cases that I'm worried about + underlying maths.

A fixed list of candidates is prepared, and randomly shuffled. Voters are presented with this list, and for a valid vote must submit candidates ordered by preference. Traditionally this involves placing a number next to each candidate, but can be turned into a drag and drop order on a digital interface. Either every candidate must have a preference for a vote to be valid, or the first X candidates must be ordered, for X >= 1, with votes being exhausted after that. Counting first preferences is often valuable for a general pie chart of who people like, but isn't directly related to the winner.

After votes are cast, every first preference is counted. If one candidate meets quota, then they automatically win. If no candidate meets quota, then the candidate with the least number of votes is eliminated, and everyone who voted for them instead switches to their #2 vote. This process repeats until a candidate meets quota. When one or more candidates meet quota, they win. They are added to the list of winners, and eliminated from the vote if more winners are needed. If more people voted for those candidates than the quota was, then the preferences for people who voted for that candidate flow on, but are reduced because a number of those votes went towards electing someone, according to the formula: `Transfer Value = Number of Surplus Votes / (Total number of winners current votes)`.

Quota is calculated as `Quota = (Number of Votes / (Number of Winners + 1)) + 1`. For elections for a single person, this will be x + 1. If two or more candidates are tied for lowest votes after first preferences have been counted and the first round of elimination is needed, then eliminate them all simultaneously. If two or more candidates are tied after the first round of eliminations, then eliminate the party with the least number of first preferences. If there is a tie there still, then keep going.

If there is a tie that would eliminate all remaining parties, then declare a failed election. In the context of my program, it should be valid to return the tied parties so that the closest winners can be displayed, however in the context of a real election you would have to call a second election and hope people vote differently.

Traditionally the results of an election are shows as a %age between the first and second place. Calculate the second place by continuing to eliminate options until only two parties remain and show the % of the vote each party got.

---

## Program structure:

Two separate applications, a web server, and a poll calculator application.

Back end (named Teller, because that's who counts polls):
Run on input data, composed of "input config" which states the candidates, their ID's, and the settings of a particular election, as well as a list of votes, which are a list of IDs in order of preference. The application is run with details of how to access data provided as arguments, and the output of the election is printed over stdout in json format.

If I wanted to do this well, the back end would run in optimised rust, and the input config would be stored in an SQL database. As I'm lazy, the back end will be coded in python, and the input will be a path to a json file, and the votes are a path to a csv.

Font end (named Poller, because that sounds nice to me):
The front end will be coded in python, using flask for ease of gluing together a web app. Use a minimalist theme, find some easy to use js UI library to let you make draggable votes, automatically expanding lists, and stick some simple graphs. If people think it's ugly tell them to make it look better idk.

Since the front end is a simple async python program, have it run the vote application in a [async subprocess](https://docs.python.org/3/library/asyncio-subprocess.html) (or a helper library if I can find a nice one). This way, if votes become too common, the code can be easily enough set up so that only one instance of the program is run at once, and if more votes are waiting the code can be run again once it finishes. This way if there are constantly new votes coming in then the vote count will update regularly each time the back end recounts the votes. Theoretically a more complex system could keep a running total but lets keep it simple for now, since that would increase complexity.

---

## Algorithm:

To reduce worst case complexity from n! to n * (n + 1), only count unique votes, and just count how many times each unique vote has been encountered.

Algorithm should work roughly as follows:

```
variables:
    total_votes
    winners_needed
    vote: {preferences, number of votes, vote multiplier = 1}

winners_list = empty list
excluded_list = empty list
quota = (total_votes / (winners_needed + 1)) + 1

first_preferences = list of 0, length of candidate list
for each vote, add number of votes to the first candidate in preferences

while len(winners_list) <= winners_needed:
    create list of candidate votes
    for each vote, add number of votes * vote multiplier to first vote in preferences not in excluded list

    if votes for candidate with most votes >= quota:
        add candidate to winners_list
        transfer_value = (votes for candidate - quota) / (votes for candidate)
        for each vote preferencing candidate after excluded removed:
            vote multiplier *= transfer_value
            
        add candidate to excluded_list
    else:
        create list of least_voted_candidates, with one item if single least voted candidate, multiple if there is a tie
        if length least_voted_candidates == 1:
            add least voted candidate to excluded_list
        else:
            create list of candidates to exclude, by finding candidate with lowest first_preferences score. If multiple candidates tie for lowest score, add all candidates to list
            add all candidates in list to exclude list
```

