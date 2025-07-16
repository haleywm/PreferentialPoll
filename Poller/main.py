from quart import Quart, jsonify, request, abort, Response
from quart_schema import QuartSchema, validate_request, validate_response
from poll_data import PollData, PollSummary, validate_poll_data, ValidationError
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
async def get_polls() -> Response:
    return jsonify(poll_manager.poll_list())


@app.post("/submit_poll")
@validate_request(PollData)
async def submit_poll(data: PollData) -> Response:
    try:
        validate_poll_data(data)
    except ValidationError as error:
        abort(Response(str(error), 400))

    return Response("Good Jorb!", 200)


def run() -> None:
    app.run()


if __name__ == "__main__":
    run()
