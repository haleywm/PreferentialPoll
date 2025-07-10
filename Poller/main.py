from quart import Quart, jsonify, request, abort, Response
from quart_schema import QuartSchema, validate_request, validate_response
from poll_data import PollData, validate_poll_data, ValidationError

app = Quart(__name__)

QuartSchema(app)

@app.post("/ping")
async def ping():
    test = await request.get_data()
    return f"Pong! {test}"

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
