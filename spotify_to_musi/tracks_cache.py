from __future__ import annotations

import json
import typing as t

import aiofiles
import pydantic
import pydantic.errors
import pydantic.json
from cache import AsyncLRU
from paths import YOUTUBE_DATA_CACHE_PATH
from typings.core import Artist, Track
from typings.youtube import YouTubeTrack


def convert_youtube_track_to_track(youtube_track: YouTubeTrack) -> Track:
    return Track(
        name=youtube_track.name,
        duration=youtube_track.duration,
        artists=tuple(Artist(name=a.name) for a in youtube_track.artists),
        album_name=youtube_track.album_name,
        is_explicit=bool(youtube_track.is_explicit),
    )


async def cache_youtube_tracks() -> None:
    """
    Cache tracks to disk.
    """

    tracks = await load_cached_youtube_tracks()
    sorted_youtube_tracks = sorted(tracks, key=lambda t: t.primary_artist.name)

    youtube_tracks_json = json.dumps(
        sorted_youtube_tracks, default=pydantic.json.pydantic_encoder
    )

    async with aiofiles.open(YOUTUBE_DATA_CACHE_PATH, "w") as f:
        await f.write(youtube_tracks_json)


@AsyncLRU(maxsize=None)  # type: ignore
async def load_cached_youtube_tracks() -> set[YouTubeTrack]:
    """
    Load cached tracks from disk.
    Only intended to be used at the start of the program to load the cache,
    and not after the program has updated the cache file on the disk.
    """
    if not YOUTUBE_DATA_CACHE_PATH.is_file():
        return set()
    async with aiofiles.open(YOUTUBE_DATA_CACHE_PATH, "r") as f:
        tracks_text = await f.read()
        tracks_json = json.loads(tracks_text)
    try:
        return {YouTubeTrack(**track) for track in tracks_json}
    except pydantic.errors.PydanticValueError:
        YOUTUBE_DATA_CACHE_PATH.unlink()
        return set()


@AsyncLRU(maxsize=None)  # type: ignore
async def load_cached_tracks() -> set[Track]:
    """
    Load cached YouTube Tracks in the form of a set of Tracks.
    """
    cached_tracks_dict = await load_cached_tracks_dict()
    return set(cached_tracks_dict.keys())


@AsyncLRU(maxsize=None)  # type: ignore
async def load_cached_tracks_dict() -> dict[Track, YouTubeTrack]:
    """
    Load cached tracks from in the form of a dict
    with the track as the key and the YouTubeTrack as the value.
    """
    cached_youtube_tracks = await load_cached_youtube_tracks()
    return {convert_youtube_track_to_track(yt): yt for yt in cached_youtube_tracks}


async def update_cached_tracks(youtube_tracks: t.Iterable[YouTubeTrack]) -> None:
    """
    Update the tracks dict with the newly fetched YouTube tracks.
    """
    tracks_dict = await load_cached_tracks_dict()
    cached_tracks = await load_cached_tracks()
    cached_youtube_tracks = await load_cached_youtube_tracks()

    for youtube_track in youtube_tracks:
        track = convert_youtube_track_to_track(youtube_track)

        tracks_dict[track] = youtube_track
        cached_tracks.add(track)
        cached_youtube_tracks.add(youtube_track)

    await cache_youtube_tracks()


async def match_tracks_to_youtube_tracks(
    tracks: t.Iterable[Track],
) -> tuple[YouTubeTrack, ...]:  # sourcery skip: for-append-to-extend, list-comprehension
    """
    Match the tracks to the cached YouTube tracks.
    """
    tracks_dict = await load_cached_tracks_dict()
    youtube_tracks: list[YouTubeTrack] = []
    for track in tracks:
        if track in tracks_dict:
            youtube_tracks.append(tracks_dict[track])
        # track not found in cache (skipped previously)
    return tuple(youtube_tracks)
