import json
import typing as t


import aiofiles
import pydantic
import pydantic.errors
import pydantic.json

from paths import YOUTUBE_DATA_CACHE_PATH
from typings.youtube import YouTubePlaylist, YouTubeTrack

from cache import AsyncLRU


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
async def load_cached_youtube_tracks() -> list[YouTubeTrack]:
    """
    Load cached tracks from disk.
    Only intended to be used at the start of the program to load the cache,
    and not after the program has updated the cache file on the disk.
    """
    if not YOUTUBE_DATA_CACHE_PATH.is_file():
        return []
    async with aiofiles.open(YOUTUBE_DATA_CACHE_PATH, "r") as f:
        tracks_text = await f.read()
        tracks_json = json.loads(tracks_text)
    try:
        return pydantic.parse_obj_as(list[YouTubeTrack], tracks_json)
    except pydantic.errors.PydanticValueError:
        YOUTUBE_DATA_CACHE_PATH.unlink()
        return []


# not sure if it this lru cache is needed, it might be inexpensive enough to just create a new set
@AsyncLRU(maxsize=None)  # type: ignore
async def load_cached_tracks() -> set[str]:
    """
    Get a set of video IDs that are cached.
    """
    return {t.video_id for t in await load_cached_youtube_tracks()}
