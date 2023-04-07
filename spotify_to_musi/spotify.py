import asyncio
import json
import os
import aiofiles
import rich

import spotipy
from pydantic import parse_obj_as

from paths import SPOTIFY_CACHE_PATH

from typings.core import Playlist, Track, Artist
from typings.spotify import SpotifyTrack, SpotifyPlaylist
import typing as t

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
    if spotify.user_creds:
        return

    async with aiofiles.open("SPOTIFY_CREDS.json", "r") as file:
        spotify_creds_text = await file.read()

    spotify_creds_json = json.loads(spotify_creds_text)
    user_creds = spotify._user_json_to_object(spotify_creds_json)

    spotify.user_creds = user_creds

    await spotify.populate_user_creds()


async def fetch_spotify_playlists() -> list[SpotifyPlaylist]:
    await init()

    playlists_resp = await spotify.user_playlists()
    playlists_items = playlists_resp["items"]  # type: ignore

    # load all pages
    offset = 0
    while playlists_resp["next"]:  # type: ignore
        offset = len(playlists_items)
        playlists_resp = await spotify.user_playlists(offset=offset)
        playlists_items.extend(playlists_resp["items"])  # type: ignore

    playlists = [SpotifyPlaylist(**p) for p in playlists_items]

    return playlists


def filter_spotify_tracks(spotify_tracks: list[SpotifyTrack]) -> list[SpotifyTrack]:
    def filter_spotify_track(spotify_track: SpotifyTrack) -> bool:
        return not spotify_track.is_local

    spotify_tracks = [t for t in spotify_tracks if filter_spotify_track(t)]

    return spotify_tracks


async def fetch_spotify_liked_tracks() -> list[SpotifyTrack]:
    await init()

    liked_tracks_resp = await spotify.user_tracks()
    liked_tracks_items = liked_tracks_resp["items"]  # type: ignore

    offset = 0
    while liked_tracks_resp["next"]:  # type: ignore
        offset = len(liked_tracks_items)
        liked_tracks_resp = await spotify.user_tracks(offset=offset)
        liked_tracks_items.extend(liked_tracks_resp["items"])  # type: ignore

    liked_tracks = [SpotifyTrack(**t["track"]) for t in liked_tracks_items]
    liked_tracks = filter_spotify_tracks(liked_tracks)

    return liked_tracks


async def covert_spotify_playlist_to_playlist(spotify_playlist: SpotifyPlaylist) -> Playlist:
    spotify_tracks_items_tasks: list[asyncio.Task[list[dict]]] = []

    for offset in range(0, spotify_playlist.track_count, 20):
        coro = spotify.playlist_tracks(playlist_id=spotify_playlist.id, offset=offset)
        task = asyncio.create_task(coro)

        spotify_tracks_items_tasks.append(task)  # type: ignore

    spotify_tracks_items: list[dict[t.Literal["items"], list[dict]]] = await asyncio.gather(*spotify_tracks_items_tasks)
    spotify_track_items: list[dict] = []

    for spotify_tracks_item in spotify_tracks_items:
        spotify_track_items.extend(spotify_tracks_item["items"])

    spotify_tracks = [SpotifyTrack(**t["track"]) for t in spotify_track_items]
    spotify_tracks = filter_spotify_tracks(spotify_tracks)

    tracks = covert_spotify_tracks_to_tracks(spotify_tracks)

    rich.print(f"[green]FETCHED:[/green] {spotify_playlist.name} ({len(tracks)} tracks)")

    return Playlist(
        id=spotify_playlist.id,
        name=spotify_playlist.name,
        cover_image_url=spotify_playlist.cover_image_url,
        tracks=tracks,
    )


def covert_spotify_track_to_track(spotify_track: SpotifyTrack) -> Track:
    return Track(
        name=spotify_track.name,
        duration=spotify_track.duration,
        artists=parse_obj_as(tuple[Artist, ...], spotify_track.artists),
    )


async def covert_spotify_playlists_to_playlists(spotify_playlists: list[SpotifyPlaylist]) -> tuple[Playlist, ...]:
    playlists_tasks: list[asyncio.Task[Playlist]] = []

    for spotify_playlist in spotify_playlists:
        coro = covert_spotify_playlist_to_playlist(spotify_playlist)
        task = asyncio.create_task(coro)

        playlists_tasks.append(task)

    playlists: list[Playlist] = await asyncio.gather(*playlists_tasks)
    return tuple(playlists)


def covert_spotify_tracks_to_tracks(spotify_tracks: list[SpotifyTrack]) -> tuple[Track, ...]:
    return tuple(covert_spotify_track_to_track(t) for t in spotify_tracks)


async def main():
    await init()

    spotify_playlists = await fetch_spotify_playlists()
    spotify_liked_tracks = await fetch_spotify_liked_tracks()

    playlists = await covert_spotify_playlists_to_playlists(spotify_playlists)
    liked_tracks = covert_spotify_tracks_to_tracks(spotify_liked_tracks)

    rich.print(playlists)
    rich.print(len(playlists))

    rich.print(liked_tracks)
    rich.print(len(liked_tracks))


if __name__ == "__main__":
    asyncio.run(main())
