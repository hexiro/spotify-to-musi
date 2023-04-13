import asyncio
import json
import os
import sys
import aiofiles
import rich

import pydantic.error_wrappers
from pydantic import parse_obj_as


from typings.core import Playlist, Track, Artist
from typings.spotify import SpotifyTrack, BasicSpotifyPlaylist, SpotifyPlaylist
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

    spotify_basic_playlists = [BasicSpotifyPlaylist(**p) for p in playlists_items]

    playlist_tasks: list[asyncio.Task[SpotifyPlaylist]] = []

    for basic_playlist in spotify_basic_playlists:
        coro = basic_playlist_to_playlist(basic_playlist)
        task = asyncio.create_task(coro)
        playlist_tasks.append(task)

    spotify_playlists: list[SpotifyPlaylist] = await asyncio.gather(*playlist_tasks)
    return spotify_playlists


async def basic_playlist_to_playlist(basic_playlist: BasicSpotifyPlaylist) -> SpotifyPlaylist:
    await init()

    spotify_tracks = await load_basic_playlist_tracks(basic_playlist)

    playlist = SpotifyPlaylist(
        name=basic_playlist.name,
        id=basic_playlist.id,
        public=basic_playlist.public,
        collaborative=basic_playlist.collaborative,
        description=basic_playlist.description,
        href=basic_playlist.href,
        uri=basic_playlist.uri,
        images=basic_playlist.images,
        tracks=spotify_tracks,
    )

    return playlist


async def load_basic_playlist_tracks(basic_spotify_playlist: BasicSpotifyPlaylist) -> list[SpotifyTrack]:
    await init()

    spotify_tracks_items_tasks: list[asyncio.Task[list[dict]]] = []

    for offset in range(0, basic_spotify_playlist.tracks.total, 20):
        coro = spotify.playlist_tracks(playlist_id=basic_spotify_playlist.id, offset=offset)
        task = asyncio.create_task(coro)

        spotify_tracks_items_tasks.append(task)  # type: ignore

    spotify_tracks_items: list[dict[t.Literal["items"], list[dict]]] = await asyncio.gather(*spotify_tracks_items_tasks)
    spotify_track_items: list[dict] = []

    for spotify_tracks_item in spotify_tracks_items:
        spotify_track_items.extend(spotify_tracks_item["items"])

    spotify_tracks = spotify_track_items_to_spotify_tracks(spotify_track_items)
    return spotify_tracks


def filter_spotify_tracks(spotify_tracks: list[SpotifyTrack]) -> list[SpotifyTrack]:
    def filter_spotify_track(spotify_track: SpotifyTrack) -> bool:
        return not spotify_track.is_local

    spotify_tracks = [t for t in spotify_tracks if filter_spotify_track(t)]

    return spotify_tracks


def spotify_track_items_to_spotify_tracks(spotify_track_items: list[dict[str, t.Any]]) -> list[SpotifyTrack]:
    spotify_tracks: list[SpotifyTrack] = []
    for spotify_track_item in spotify_track_items:
        try:
            track = SpotifyTrack(**spotify_track_item["track"])
        # weird spotify api bug where track, artist, and album name is blank
        # (usually because the track is by 'various artists' the spotify thing)
        # but w/o this information we can't fetch the track so just skip it
        except pydantic.error_wrappers.ValidationError:
            continue
        else:
            spotify_tracks.append(track)

    spotify_tracks = filter_spotify_tracks(spotify_tracks)
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

    liked_tracks: list[SpotifyTrack] = spotify_track_items_to_spotify_tracks(liked_tracks_items)
    return liked_tracks


def covert_spotify_playlist_to_playlist(spotify_playlist: SpotifyPlaylist) -> Playlist:
    tracks = covert_spotify_tracks_to_tracks(spotify_playlist.tracks)

    rich.print(f"[bold green]SPOTIFY:[/bold green] {spotify_playlist.name} ({len(tracks)} tracks)")

    return Playlist(
        id=spotify_playlist.id,
        name=spotify_playlist.name,
        cover_image_url=spotify_playlist.cover_image_url,
        tracks=tracks,
    )


def covert_spotify_track_to_track(spotify_track: SpotifyTrack) -> Track:
    track = Track(
        name=spotify_track.name,
        duration=spotify_track.duration,
        artists=parse_obj_as(tuple[Artist, ...], spotify_track.artists),
        album_name=spotify_track.album_name,
        is_explicit=spotify_track.explicit,
    )
    return track


def covert_spotify_playlists_to_playlists(spotify_playlists: list[SpotifyPlaylist]) -> tuple[Playlist, ...]:
    return tuple(covert_spotify_playlist_to_playlist(p) for p in spotify_playlists)


def covert_spotify_tracks_to_tracks(spotify_tracks: t.Iterable[SpotifyTrack]) -> tuple[Track, ...]:
    return tuple(covert_spotify_track_to_track(t) for t in spotify_tracks)


if __name__ == "__main__":

    async def main():
        spotify_playlists = await fetch_spotify_playlists()
        spotify_liked_tracks = await fetch_spotify_liked_tracks()

        playlists = covert_spotify_playlists_to_playlists(spotify_playlists)
        liked_tracks = covert_spotify_tracks_to_tracks(spotify_liked_tracks)

        rich.print(playlists)
        rich.print(len(playlists))

        rich.print(liked_tracks)
        rich.print(len(liked_tracks))

    asyncio.run(main())
