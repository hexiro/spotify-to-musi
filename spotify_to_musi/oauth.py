from __future__ import annotations

import functools
import json
import sys
import typing as t
import uuid

import aiofiles
import sanic
import sanic.response
from paths import SPOTIFY_CREDENTIALS_PATH
from pyfy import AsyncSpotify, AuthError, ClientCreds
from sanic import SanicException, response
from sanic.worker.loader import AppLoader

ADDRESS = "localhost"
PORT = 5000
ADDRESS_WITH_PORT = f"{ADDRESS}:{PORT}"
URL = f"http://{ADDRESS_WITH_PORT}/authorize"
STATE = str(uuid.uuid4())

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "sanic.root": {"level": "ERROR", "handlers": ["console"]},
        "sanic.error": {
            "level": "ERROR",
            "handlers": ["error_console"],
            "propagate": True,
            "qualname": "sanic.error",
        },
        "sanic.access": {
            "level": "ERROR",
            "handlers": ["access_console"],
            "propagate": True,
            "qualname": "sanic.access",
        },
        "sanic.server": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": True,
            "qualname": "sanic.server",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stdout,
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stderr,
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": sys.stdout,
        },
    },
    "formatters": {
        "generic": {
            "format": "%(asctime)s [%(process)s] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "access": {
            "format": "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: %(request)s %(message)s %(status)s %(byte)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
}


def attach_endpoints(
    app: sanic.Sanic,
    spotify: AsyncSpotify,
    spotify_client_id: str,
    spotify_client_secret: str,
) -> None:
    @app.route("/authorize")  # type: ignore
    async def _authorize(_request: sanic.Request) -> sanic.HTTPResponse:
        if spotify.is_oauth_ready:
            return response.redirect(spotify.auth_uri(state=STATE))

        error_body = {
            "error_description": "Client needs client_id, client_secret and a redirect uri in order to handle OAuth properly"
        }
        return response.json(
            body=error_body,
            status=500,
        )

    @app.route("/callback/spotify")  # REGISTER THIS ROUTE AS REDIRECT URI IN SPOTIFY DEV CONSOLE
    async def _spotify_callback(request: sanic.Request) -> sanic.HTTPResponse:
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
            user_creds_json: dict[str, t.Any] = await spotify._request_user_creds(grant=code)  # type: ignore
        except AuthError as exc:
            error_code: int = exc.code  # type: ignore
            body = {"error_description": exc.msg, "error_code": error_code}
            return response.json(body, status=error_code)

        user_creds_model = spotify._user_json_to_object(user_creds_json)
        spotify.user_creds = user_creds_model

        user_creds_json["client_id"] = spotify_client_id
        user_creds_json["client_secret"] = spotify_client_secret

        async with aiofiles.open(SPOTIFY_CREDENTIALS_PATH, "w") as file:
            await file.write(json.dumps(user_creds_json))

        await spotify.populate_user_creds()

        try:
            return response.json(body={"success": True})
        finally:
            app.stop()


def create_app(app_name: str, spotify_client_id: str, spotify_client_secret: str) -> sanic.Sanic:
    client_creds = ClientCreds(
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        redirect_uri="http://localhost:5000/callback/spotify",
        scopes=[
            "user-library-read",
            "playlist-read-collaborative",
            "playlist-read-private",
        ],
    )

    spotify = AsyncSpotify(client_creds=client_creds)

    app = sanic.Sanic(app_name, log_config=LOG_CONFIG)
    attach_endpoints(app, spotify, spotify_client_id, spotify_client_secret)
    return app


async def run(*, spotify_client_id: str, spotify_client_secret: str) -> None:
    app_name = "Spotify-OAuth"
    loader = AppLoader(
        factory=functools.partial(
            create_app,
            app_name,
            spotify_client_id,
            spotify_client_secret,
        )
    )
    app = loader.load()
    app.prepare(port=PORT, motd=False, access_log=False)
    sanic.Sanic.serve(primary=app, app_loader=loader)
