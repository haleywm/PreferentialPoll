# Preferential Poll

A project by Haley.

The goal of this project is to make a simple system that lets a website run straw-poll style internet polls, but using a proper implementation of preferential voting.

I'm working on this because I was unable to find any other implementations online that I liked. The ones that I could find were highly critical of the preferential voting system, which I disagree with, and had a very limited implementation, which had a short number of maximum parties. I want to make something which lets people host a customisable implementation of preferential voting, with options for partial votes (such as allowing people to give a minimum of 6 preferences rather than ranking all options), or voting for multiple candidates (choosing the top 3 most popular candidates). It would also be nice to show some fun graphics about how the vote was calculated, however I'll likely leave that until after the initial proof of concept is complete.

## Program Structure

The program is structured into two sub-programs, **Poller** and **Teller**.

### Poller

Poller is the front end, which allows people to create new polls, allows them to vote in existing polls, and calls teller to count the votes and produce a result as needed.

### Teller

Teller is a back end application which actually implements the counting of a preferential vote. Teller is a command line application which takes arguments for what to process, and prints the results in json over stdout, to make it easily fit into a front end as required.
