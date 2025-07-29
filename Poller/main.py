from quart import Quart, abort, Response, send_file
from quart_schema import QuartSchema, validate_request, validate_response
from quart_cors import cors
import os
from poll_data import (
    NewPoll,
    PollData,
    PollResults,
    PollSummary,
    Vote,
    SpecificPoll,
    ValidationError,
)
from poll_manager import PollManager

app = Quart(__name__)

QuartSchema(app)

# Apply CORS if requested
allowed_origin = os.getenv("ALLOWED_ORIGIN")
if allowed_origin is not None:
    app = cors(
        app,
        allow_origin=allowed_origin,
        allow_methods=["GET", "POST"],
        max_age=600,
        allow_credentials=False,
        allow_headers=["Content-Type"],
        expose_headers=[],
        send_origin_wildcard=False,
    )

poll_manager = PollManager()


@app.get("/get_polls")
@validate_response(list[PollSummary])
async def get_polls() -> list[PollSummary]:
    return poll_manager.poll_list()


# This would be a get
# But I literally can't see any documentation for making a GET query in quart
@app.post("/get_poll_details")  # pyright:ignore
@validate_request(SpecificPoll)
@validate_response(PollData)
async def get_poll_details(data: SpecificPoll) -> PollData:
    poll_id = data.election_id
    try:
        poll = poll_manager.polls[poll_id]
    except KeyError:
        abort(Response("Invalid Poll ID", 400))
    return poll.config


@app.post("/get_poll_results")  # pyright:ignore
@validate_request(SpecificPoll)
@validate_response(PollResults)
async def get_poll_results(data: SpecificPoll) -> PollResults:
    poll_id = data.election_id
    try:
        poll = poll_manager.polls[poll_id]
    except KeyError:
        abort(Response("Invalid Poll ID", 400))
    return await poll.get_results(True)


# Absolutely no clue why my code editor doesn't like this line
# But the code works and mypy --strict doesn't complain
# And a #type: ignore comment makes mypy complain about an unused ignore
@app.post("/submit_poll")  # pyright: ignore
@validate_request(NewPoll)
@validate_response(SpecificPoll)
async def submit_poll(data: NewPoll) -> SpecificPoll:
    try:
        poll_manager.validate_poll_data(data)
        poll_id = await poll_manager.add_poll(data)
    except ValidationError as error:
        abort(Response(str(error), 400))

    return SpecificPoll(poll_id)


@app.post("/submit_vote")
@validate_request(Vote)
async def submit_vote(data: Vote) -> Response:
    try:
        poll_manager.validate_vote(data)
    except ValidationError as error:
        abort(Response(str(error), 400))
    poll_manager.add_vote(data)

    return Response("OK", 200)


@app.post("/download_all_votes")
@validate_request(SpecificPoll)
async def download_all_votes(data: SpecificPoll) -> Response:
    # Download entire contents of relevant poll file
    response: Response
    if data.election_id in poll_manager.polls:
        # Poll is present
        # Read votes path from poll and use with quart's built-in send_file
        response = await send_file(poll_manager.polls[data.election_id].votes_path)
    else:
        # Poll not found
        response = Response("Poll not found", 404)
    return response


def run() -> None:
    app.run()


if __name__ == "__main__":
    run()
