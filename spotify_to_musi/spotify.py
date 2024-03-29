from __future__ import annotations

import asyncio
import math
import typing as t

import pydantic
import pyfy.excs
import rich
from pyfy import AsyncSpotify, ClientCreds

from spotify_to_musi.commons import (
    SPOTIFY_ID_REGEX,
    load_spotify_credentials,
    loaded_message,
    skipping_message,
    spotify_client_credentials_from_file,
    task_description,
)
from spotify_to_musi.typings.core import Artist, Playlist, Track
from spotify_to_musi.typings.spotify import (
    BasicSpotifyPlaylist,
    SpotifyPlaylist,
    SpotifyResponse,
    SpotifyTrack,
)

if t.TYPE_CHECKING:
    from rich.progress import Progress, TaskID


client_creds = ClientCreds(
    redirect_uri="http://localhost:5000/callback/spotify",
    scopes=[
        "user-library-read",
        "playlist-read-collaborative",
        "playlist-read-private",
    ],
)

spotify = AsyncSpotify(client_creds=client_creds)


async def init() -> None:
    if spotify.user_creds:
        return

    spotify_creds = await load_spotify_credentials()

    if not spotify_creds:
        return

    spotify_client_creds = spotify_client_credentials_from_file(spotify_creds)

    if not spotify_client_creds:
        return

    client_id, client_secret = spotify_client_creds

    spotify.client_creds.client_id = client_id
    spotify.client_creds.client_secret = client_secret

    user_creds = spotify._user_json_to_object(spotify_creds)
    spotify.user_creds = user_creds

    await spotify.populate_user_creds()


async def query_spotify(
    transfer_user_library: bool, extra_playlist_urls: list[str], progress: Progress
) -> tuple[tuple[Playlist, ...], tuple[Track, ...]]:
    await init()

    spotify_liked_tracks: list[SpotifyTrack] = []
    spotify_basic_playlists: list[BasicSpotifyPlaylist] = []

    task_id = progress.add_task(
        task_description(querying="Spotify", subtype="Playlists", color="green"),
        start=False,
    )

    if transfer_user_library:
        spotify_basic_user_playlists = await fetch_basic_user_spotify_playlists(task_id=task_id, progress=progress)
        spotify_basic_playlists.extend(spotify_basic_user_playlists)

        task_id = progress.add_task(
            task_description(querying="Spotify", subtype="Liked Songs", color="green"),
            start=False,
        )
        spotify_liked_user_tracks = await fetch_spotify_user_liked_tracks(task_id=task_id, progress=progress)
        spotify_liked_tracks.extend(spotify_liked_user_tracks)

    if extra_playlist_urls:
        spotify_basic_extra_playlists = await fetch_basic_spotify_playlists(
            extra_playlist_urls, task_id=task_id, progress=progress
        )
        spotify_basic_playlists.extend(spotify_basic_extra_playlists)

    task_id = progress.add_task(
        task_description(querying="Spotify", subtype="Playlist Tracks", color="green"),
        start=False,
    )

    spotify_playlists = await load_basic_playlists(spotify_basic_playlists, task_id=task_id, progress=progress)

    playlists = covert_spotify_playlists_to_playlists(spotify_playlists)
    liked_tracks = covert_spotify_tracks_to_tracks(spotify_liked_tracks)

    return playlists, liked_tracks


async def fetch_basic_user_spotify_playlists(
    task_id: TaskID,
    progress: Progress,
) -> list[BasicSpotifyPlaylist]:
    await init()

    limit = 50

    playlists_resp = await spotify.user_playlists(limit=limit)
    playlists_items = playlists_resp["items"]  # type: ignore

    total_tracks: int = playlists_resp["total"]  # type: ignore
    total = math.ceil(total_tracks / limit)

    progress.update(task_id, total=total, completed=1)
    progress.start_task(task_id)

    async def load_user_playlists(offset: int, limit: int) -> SpotifyResponse:
        try:
            return await spotify.user_playlists(offset=offset, limit=limit)  # type: ignore
        finally:
            progress.update(task_id, advance=1)

    # load all pages
    offset = 0
    while playlists_resp["next"]:  # type: ignore
        offset = len(playlists_items)
        playlists_resp = await load_user_playlists(offset=offset, limit=limit)
        playlists_items.extend(playlists_resp["items"])  # type: ignore

    spotify_basic_playlists = [BasicSpotifyPlaylist(**p) for p in playlists_items]
    return spotify_basic_playlists


async def fetch_basic_spotify_playlists(
    playlist_urls: list[str],
    task_id: TaskID,
    progress: Progress,
) -> list[BasicSpotifyPlaylist]:
    tasks: list[asyncio.Task[BasicSpotifyPlaylist | None]] = []
    total = len(playlist_urls)

    progress.update(task_id, total=total, completed=0)
    progress.start_task(task_id)

    for playlist_url in playlist_urls:
        coro = fetch_basic_spotify_playlist(playlist_url, task_id=task_id, progress=progress)
        task = asyncio.create_task(coro)
        tasks.append(task)

    spotify_basic_playlists_or_null: list[BasicSpotifyPlaylist | None] = await asyncio.gather(*tasks)

    spotify_basic_playlists: list[BasicSpotifyPlaylist] = [p for p in spotify_basic_playlists_or_null if p is not None]

    return spotify_basic_playlists


async def fetch_basic_spotify_playlist(
    playlist_url: str,
    task_id: TaskID,
    progress: Progress,
) -> BasicSpotifyPlaylist | None:
    await init()

    match = SPOTIFY_ID_REGEX.match(playlist_url)
    playlist_id = match.group("id") if match else playlist_url

    try:
        spotify_basic_playlist = await spotify.playlist(playlist_id)
        return BasicSpotifyPlaylist(**spotify_basic_playlist)  # type: ignore
    except pyfy.excs.SpotifyError:
        rich.print(
            skipping_message(
                text=f"[blue underline]{playlist_url}[/blue underline]",
                reason="Invalid playlist link.",
            )
        )
        return None
    finally:
        progress.update(task_id, advance=1)


async def load_basic_playlists(
    basic_spotify_playlists: t.Iterable[BasicSpotifyPlaylist],
    *,
    task_id: TaskID,
    progress: Progress,
) -> list[SpotifyPlaylist]:  # sourcery skip: sum-comprehension
    playlist_tasks: list[asyncio.Task[SpotifyPlaylist]] = []

    total = 0
    for basic_playlist in basic_spotify_playlists:
        total += math.ceil(basic_playlist.tracks.total / 50)

    progress.update(task_id, total=total, completed=0)
    progress.start_task(task_id)

    for basic_playlist in basic_spotify_playlists:
        coro = basic_playlist_to_playlist(basic_playlist, task_id=task_id, progress=progress)
        task = asyncio.create_task(coro)
        playlist_tasks.append(task)

    spotify_playlists: list[SpotifyPlaylist] = await asyncio.gather(*playlist_tasks)
    return spotify_playlists


async def basic_playlist_to_playlist(
    basic_playlist: BasicSpotifyPlaylist,
    *,
    task_id: TaskID,
    progress: Progress,
) -> SpotifyPlaylist:
    await init()

    spotify_tracks = await load_basic_playlist_tracks(basic_playlist, task_id=task_id, progress=progress)

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

    rich.print(
        loaded_message(
            source="Spotify",
            loaded="Playlist",
            name=playlist.name,
            tracks_count=len(spotify_tracks),
            color="green",
        )
    )

    return playlist


async def load_basic_playlist_tracks(
    basic_spotify_playlist: BasicSpotifyPlaylist,
    *,
    task_id: TaskID,
    progress: Progress,
) -> list[SpotifyTrack]:
    await init()

    spotify_tracks_items_tasks: list[asyncio.Task[list[dict]]] = []

    async def load_playlist_tracks(offset: int, limit: int) -> SpotifyResponse:
        try:
            return await spotify.playlist_tracks(
                playlist_id=basic_spotify_playlist.id, offset=offset, limit=limit
            )  # type: ignore
        finally:
            progress.update(task_id, advance=1)

    limit = 50
    for offset in range(0, basic_spotify_playlist.tracks.total, limit):
        coro = load_playlist_tracks(offset=offset, limit=limit)
        task = asyncio.create_task(coro)

        spotify_tracks_items_tasks.append(task)  # type: ignore

    spotify_tracks_items: list[dict[t.Literal["items"], list[dict]]] = await asyncio.gather(
        *spotify_tracks_items_tasks
    )
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
        except pydantic.ValidationError as exc:
            for error in exc.errors():
                if error["input"] == "":
                    continue
                # as in: '[type] name can't be blank'
                if "blank" in error["msg"]:
                    continue
                raise
        else:
            spotify_tracks.append(track)

    spotify_tracks = filter_spotify_tracks(spotify_tracks)
    return spotify_tracks


async def fetch_spotify_user_liked_tracks(
    task_id: TaskID,
    progress: Progress,
) -> list[SpotifyTrack]:
    await init()

    limit = 50

    liked_tracks_resp = await spotify.user_tracks(limit=limit)
    liked_tracks_items = liked_tracks_resp["items"]  # type: ignore

    total_tracks: int = liked_tracks_resp["total"]  # type: ignore
    total = math.ceil(total_tracks // limit)

    progress.update(task_id, total=total, completed=1)
    progress.start_task(task_id)

    async def load_user_tracks(offset: int, limit: int) -> SpotifyResponse:
        try:
            return await spotify.user_tracks(offset=offset, limit=limit)  # type: ignore
        finally:
            progress.update(task_id, advance=1)

    offset = 0
    while liked_tracks_resp["next"]:  # type: ignore
        offset = len(liked_tracks_items)
        liked_tracks_resp = await load_user_tracks(offset=offset, limit=limit)
        liked_tracks_items.extend(liked_tracks_resp["items"])  # type: ignore

    liked_tracks: list[SpotifyTrack] = spotify_track_items_to_spotify_tracks(liked_tracks_items)

    rich.print(
        loaded_message(
            source="Spotify",
            loaded="Liked Songs",
            tracks_count=len(liked_tracks),
            color="green",
        )
    )

    return liked_tracks


def covert_spotify_playlist_to_playlist(spotify_playlist: SpotifyPlaylist) -> Playlist:
    tracks = covert_spotify_tracks_to_tracks(spotify_playlist.tracks)

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
        artists=tuple(Artist(name=a.name) for a in spotify_track.artists),
        album_name=spotify_track.album_name,
        is_explicit=spotify_track.explicit,
    )
    return track


def covert_spotify_playlists_to_playlists(
    spotify_playlists: t.Iterable[SpotifyPlaylist],
) -> tuple[Playlist, ...]:
    return tuple(covert_spotify_playlist_to_playlist(p) for p in spotify_playlists)


def covert_spotify_tracks_to_tracks(
    spotify_tracks: t.Iterable[SpotifyTrack],
) -> tuple[Track, ...]:
    return tuple(covert_spotify_track_to_track(t) for t in spotify_tracks)
