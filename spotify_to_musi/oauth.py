import asyncio
import datetime
import os
import aiofiles
import webbrowser
import json as json

import sanic
import sanic.response
from sanic import Sanic, SanicException, response


from pyfy import AuthError, ClientCreds, AsyncSpotify

import typing as t

import dotenv

dotenv.load_dotenv()


ADDRESS = "localhost"
PORT = 5000
ADDRESS_WITH_PORT = ADDRESS + ":" + str(PORT)
# TODO: figure out if this matters / make it a random string if it does
STATE = "123"


app = Sanic(__name__)

client_id = os.environ["SPOTIFY_CLIENT_ID"]
client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]

client_creds = ClientCreds(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri="http://localhost:5000/callback/spotify",
    scopes=["user-library-read", "playlist-read-collaborative", "playlist-read-private"],
)

spotify = AsyncSpotify(client_creds=client_creds)


@app.route("/authorize")  # type: ignore
async def _authorize(_request: sanic.Request):
    if spotify.is_oauth_ready:
        return response.redirect(spotify.auth_uri(state=STATE))
    error_body = {
        "error_description": "Client needs client_id, client_secret and a redirect uri in order to handle OAauth properly"
    }
    return response.json(
        body=error_body,
        status=500,
    )


@app.route("/callback/spotify")  # REGISTER THIS ROUTE AS REDIRECT URI IN SPOTIFY DEV CONSOLE
async def _spotify_callback(request: sanic.Request):
    error = request.args.get("error")
    code = request.args.get("code")

    if error:
        error_description = request.args.get("error_description")
        return response.json({error: error_description})
    if not code:
        return response.text("Something is wrong with your callback", status=400)

    callback_state = request.args.get("state")

    if callback_state != STATE:
        raise SanicException(status_code=401)
    try:
        user_creds_json = await spotify._request_user_creds(grant=code)
    except AuthError as exc:
        error_code: int = exc.code  # type: ignore
        body = {"error_description": exc.msg, "error_code": error_code}
        return response.json(body, status=error_code)

    user_creds_model = spotify._user_json_to_object(user_creds_json)
    spotify.user_creds = user_creds_model

    async with aiofiles.open("SPOTIFY_CREDS.json", "w") as file:
        await file.write(json.dumps(user_creds_json))

    await spotify.populate_user_creds()

    async def stop_server():
        await asyncio.sleep(3)
        app.stop()

    asyncio.create_task(stop_server())

    return response.json(body={"success": True})


async def run():
    webbrowser.open_new_tab("http://" + ADDRESS_WITH_PORT + "/authorize")
    app.run(host=ADDRESS, port=PORT, debug=True)

    await spotify.populate_user_creds()
    await spotify.user_top_tracks()


if __name__ == "__main__":
    asyncio.run(run())
