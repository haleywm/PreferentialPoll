# Poller

Poller is the front end application. It works as a Quart-based REST API. It's not intended to be a full functioning front-end, just to serve the data so that someone can implement it into their own website. I am entirely doing this because I have my own [website](https://github.com/haleywm/WebbedSite) and this works better as just an endpoint for JS to interact with.

It will handle:

- Requests to create new polls
- Requests to list existing polls
- Requests to vote in a poll
- Requests to view the current results of a poll

Poller will call Teller every time a new vote is received in order to count new votes. By running this other process as an async worker, it can ensure that only poller, or teller are modifying the files at a given time, in order to very lazily achieve the necessarily level of atomicity.

Poller is also responsible for verifying the legitimacy of incoming requests and outgoing data to ensure that everything meets requirements.

As a safety precaution to prevent abuse, I will implement limits on the number of polls that can be created using a variable, so that this can be lifted depending on context. A limit on the length of polls to prevent ridiculously large polls that attempt to consume too much memory will also be implemented. Any further points of abuse such as denial of service techniques are left to real web servers to implement, as Poller is intended to be deployed behind a real server such as Caddy (plus whatever Uvicorn provides).

## Endpoints

Poller supports the following endpoints using the following syntax:

TODO
