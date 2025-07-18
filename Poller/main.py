from quart import Quart, jsonify, request, abort, Response
from quart_schema import QuartSchema, validate_request, validate_response
from poll_data import (
    NewPoll,
    PollSummary,
    PollCreationInfo,
    validate_poll_data,
    ValidationError,
)
from poll_manager import PollManager

app = Quart(__name__)

QuartSchema(app)
poll_manager = PollManager()


@app.post("/ping")
async def ping() -> str:
    test = await request.get_data()
    if isinstance(test, bytes):
        test = test.decode()
    return f"Pong! {test}"


@app.get("/get_polls")
@validate_response(list[PollSummary])
async def get_polls() -> list[PollSummary]:
    return poll_manager.poll_list()


# Absolutely no clue why my code editor doesn't like this line
# But the code works and mypy --strict doesn't complain
# And a #type: ignore comment makes mypy complain about an unused ignore
@app.post("/submit_poll")  # pyright: ignore
@validate_request(NewPoll)
@validate_response(PollCreationInfo)
async def submit_poll(data: NewPoll) -> PollCreationInfo:
    try:
        validate_poll_data(data)
    except ValidationError as error:
        abort(Response(str(error), 400))

    poll_id = await poll_manager.add_poll(data)

    return PollCreationInfo(poll_id)


def run() -> None:
    app.run()


if __name__ == "__main__":
    run()
