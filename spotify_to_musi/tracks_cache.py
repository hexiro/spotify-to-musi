import json
import typing as t


import aiofiles
import pydantic
import pydantic.errors
import pydantic.json

from paths import YOUTUBE_DATA_CACHE_PATH

from typings.core import Track, Artist
from typings.youtube import YouTubePlaylist, YouTubeTrack

from cache import AsyncLRU


def convert_youtube_track_to_track(youtube_track: YouTubeTrack) -> Track:
    return Track(
        name=youtube_track.name,
        duration=youtube_track.duration,
        artists=tuple(Artist(name=a.name) for a in youtube_track.artists),
        album_name=youtube_track.album_name,
        is_explicit=bool(youtube_track.is_explicit),
    )


async def cache_youtube_tracks(
    youtube_playlists: tuple[YouTubePlaylist, ...], youtube_liked_tracks: tuple[YouTubeTrack, ...]
) -> None:
    """
    Cache tracks to disk.
    """

    youtube_tracks_to_cache: list[YouTubeTrack] = list(youtube_liked_tracks)
    for youtube_playlist in youtube_playlists:
        youtube_tracks_to_cache.extend(youtube_playlist.tracks)

    youtube_track_video_ids: set[str] = {t.video_id for t in youtube_tracks_to_cache}

    current_youtube_tracks = await load_cached_youtube_tracks()

    for youtube_track in current_youtube_tracks:
        if youtube_track.video_id in youtube_track_video_ids:
            continue
        youtube_tracks_to_cache.append(youtube_track)
        youtube_track_video_ids.add(youtube_track.video_id)

    youtube_tracks_json = json.dumps(youtube_tracks_to_cache, default=pydantic.json.pydantic_encoder)

    async with aiofiles.open(YOUTUBE_DATA_CACHE_PATH, "w") as f:
        await f.write(youtube_tracks_json)


@AsyncLRU(maxsize=None)  # type: ignore
async def load_cached_youtube_tracks() -> tuple[YouTubeTrack]:
    """
    Load cached tracks from disk.
    Only intended to be used at the start of the program to load the cache,
    and not after the program has updated the cache file on the disk.
    """
    if not YOUTUBE_DATA_CACHE_PATH.is_file():
        return tuple()
    async with aiofiles.open(YOUTUBE_DATA_CACHE_PATH, "r") as f:
        tracks_text = await f.read()
        tracks_json = json.loads(tracks_text)
    try:
        return tuple(YouTubeTrack(**track) for track in tracks_json)
    except pydantic.errors.PydanticValueError:
        YOUTUBE_DATA_CACHE_PATH.unlink()
        return tuple()


@AsyncLRU(maxsize=None)  # type: ignore
async def load_cached_tracks_dict() -> dict[Track, YouTubeTrack]:
    cached_youtube_tracks = await load_cached_youtube_tracks()
    return {convert_youtube_track_to_track(yt): yt for yt in cached_youtube_tracks}


@AsyncLRU(maxsize=None)  # type: ignore
async def load_cached_tracks() -> set[Track]:
    cached_tracks_dict = await load_cached_tracks_dict()
    return set(cached_tracks_dict.keys())
