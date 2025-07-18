from quart import Quart, jsonify, request, abort, Response
from quart_schema import QuartSchema, validate_request, validate_response
from poll_data import (
    NewPoll,
    PollData,
    PollSummary,
    PollCreationInfo,
    Vote,
    ValidationError,
)
from poll_manager import PollManager

app = Quart(__name__)

QuartSchema(app)
poll_manager = PollManager()


@app.get("/get_polls")
@validate_response(list[PollSummary])
async def get_polls() -> list[PollSummary]:
    return poll_manager.poll_list()


@app.get("/get_poll_details")  # pyright:ignore
@validate_request(int)
@validate_response(PollData)
async def get_poll_details(poll_id: int) -> PollData:
    try:
        result = poll_manager.polls[poll_id]
    except KeyError:
        abort(Response("Invalid Poll ID", 400))
    return result.config


# Absolutely no clue why my code editor doesn't like this line
# But the code works and mypy --strict doesn't complain
# And a #type: ignore comment makes mypy complain about an unused ignore
@app.post("/submit_poll")  # pyright: ignore
@validate_request(NewPoll)
@validate_response(PollCreationInfo)
async def submit_poll(data: NewPoll) -> PollCreationInfo:
    try:
        poll_manager.validate_poll_data(data)
    except ValidationError as error:
        abort(Response(str(error), 400))

    poll_id = await poll_manager.add_poll(data)

    return PollCreationInfo(poll_id)


@app.post("/submit_vote")
@validate_request(Vote)
async def ping(new_vote: Vote) -> Response:
    try:
        poll_manager.validate_vote(new_vote)
    except ValidationError as error:
        abort(Response(str(error), 400))
    await poll_manager.add_vote(new_vote)

    return Response("OK", 200)


def run() -> None:
    app.run()


if __name__ == "__main__":
    run()
