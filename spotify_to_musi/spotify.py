import json
import os
import aiofiles
import rich

import spotipy
from pydantic import parse_obj_as

from paths import SPOTIFY_CACHE_PATH

from typings.core import Playlist, Track, Artist
from typings.spotify import SpotifyTrack, SpotifyPlaylist

console = rich.get_console()

import dotenv

dotenv.load_dotenv()

from pyfy import AsyncSpotify, ClientCreds

client_id = os.environ["SPOTIFY_CLIENT_ID"]
client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]

client_creds = ClientCreds(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri="http://localhost:5000/callback/spotify",
    scopes=["user-library-read", "playlist-read-collaborative", "playlist-read-private"],
)

spotify = AsyncSpotify(client_creds=client_creds)


async def init() -> None:
    async with aiofiles.open("SPOTIFY_CREDS.json", "r") as file:
        spotify_creds_text = await file.read()

    spotify_creds_json = json.loads(spotify_creds_text)
    user_creds = spotify._user_json_to_object(spotify_creds_json)

    spotify.user_creds = user_creds

    await spotify.populate_user_creds()


async def main():
    await init()

    def filter_spotify_track(spotify_track: SpotifyTrack) -> bool:
        return not spotify_track.is_local

    playlists_resp = await spotify.user_playlists()
    playlists_items = playlists_resp["items"]  # type: ignore

    # load all pages
    offset = 0
    while playlists_resp["next"]:  # type: ignore
        offset = len(playlists_items)
        playlists_resp = await spotify.user_playlists(offset=offset)
        playlists_items.extend(playlists_resp["items"])  # type: ignore

    liked_tracks_resp = await spotify.user_tracks()
    liked_tracks_items = liked_tracks_resp["items"]  # type: ignore

    offset = 0
    while liked_tracks_resp["next"]:  # type: ignore
        offset = len(liked_tracks_items)
        liked_tracks_resp = await spotify.user_tracks(offset=offset)
        liked_tracks_items.extend(liked_tracks_resp["items"])  # type: ignore

    playlists = [SpotifyPlaylist(**p) for p in playlists_items]
    liked_tracks = [SpotifyTrack(**t["track"]) for t in liked_tracks_items]
    liked_tracks = [t for t in liked_tracks if filter_spotify_track(t)]

    rich.print(playlists)
    rich.print(len(playlists))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
