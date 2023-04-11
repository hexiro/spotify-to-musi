import asyncio
import json
import typing as t
import uuid

import httpx
import requests
from requests_toolbelt import MultipartEncoder
import rich

import pydantic.error_wrappers

from typings.youtube import YouTubeTrack, YouTubePlaylist
from typings.musi import (
    MusiResponse,
    MusiVideo,
    MusiLibrary,
    MusiTrack,
    MusiPlaylist,
    MusiLibraryDict,
    MusiVideoDict,
    MusiPlaylistDict,
)


def covert_youtube_tracks_to_musi_tracks(youtube_tracks: t.Iterable[YouTubeTrack]) -> tuple[MusiTrack, ...]:
    musi_tracks: list[MusiTrack] = []

    for youtube_track in youtube_tracks:
        musi_track = MusiTrack(**youtube_track.dict())
        musi_tracks.append(musi_track)

    return tuple(musi_tracks)


def covert_youtube_tracks_to_musi_library(youtube_tracks: t.Iterable[YouTubeTrack]) -> MusiLibrary:
    musi_tracks = covert_youtube_tracks_to_musi_tracks(youtube_tracks)
    return MusiLibrary(tracks=musi_tracks)


def convert_playlists_to_musi_playlists(youtube_playlists: t.Iterable[YouTubePlaylist]) -> tuple[MusiPlaylist]:
    musi_playlists: list[MusiPlaylist] = []

    for youtube_playlist in youtube_playlists:
        musi_tracks = covert_youtube_tracks_to_musi_tracks(youtube_playlist.tracks)
        musi_playlist = MusiPlaylist(
            name=youtube_playlist.name,
            tracks=musi_tracks,
            cover_image_url=youtube_playlist.cover_image_url,
        )
        musi_playlists.append(musi_playlist)

    return tuple(musi_playlists)


async def upload_to_musi(
    musi_playlists: t.Iterable[MusiPlaylist],
    musi_library: MusiLibrary,
) -> MusiResponse:
    musi_videos: list[MusiVideo] = []

    for musi_track in musi_library.tracks:
        musi_videos.append(musi_track.musi_video())
    for musi_playlist in musi_playlists:
        for musi_track in musi_playlist.tracks:
            musi_videos.append(musi_track.musi_video())

    musi_library_dict: MusiLibraryDict = musi_library.dict()
    musi_playlist_dicts: list[MusiPlaylistDict] = [musi_item.dict() for musi_item in musi_playlists]  # type: ignore
    musi_video_dicts: list[MusiVideoDict] = []

    musi_video_ids: set[str] = set()
    for musi_video in musi_videos:
        if musi_video.video_id not in musi_video_ids:
            musi_video_dicts.append(musi_video.dict())  # type: ignore
            musi_video_ids.add(musi_video.video_id)

    musi_uuid = uuid.uuid4()
    payload = {
        "library": musi_library_dict,
        "playlist_items": musi_video_dicts,
        "playlists": musi_playlist_dicts,
    }

    boundary_str = f"Boundary+Musi{musi_uuid}"
    boundary = f"--{boundary_str}".encode()

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary_str};",
        "User-Agent": "Musi/25691 CFNetwork/1206 Darwin/20.1.0",
    }

    # hack because httpx doesn't appear to support custom boundaries like requests does.
    content = (
        boundary
        + b"\n"
        + b'Content-Disposition: form-data; name="data"'
        + b"\n\n"
        + json.dumps(payload).encode()
        + b"\n"
        + boundary
        + b"\n"
        + b'Content-Disposition: form-data; name="uuid"'
        + b"\n\n"
        + str(musi_uuid).encode()
        + b"\n"
        + boundary
        + b"--\n"
    )

    async with httpx.AsyncClient(headers=headers) as client:
        url = "https://feelthemusi.com/api/v4/backups/create"
        resp = await client.post(url, content=content)

    rich.print(resp.text)

    try:
        backup = MusiResponse(**resp.json())
    except (pydantic.error_wrappers.ValidationError, json.decoder.JSONDecodeError):
        rich.print(f"[bold red]ERROR:[/bold red] {resp.text}]")
        raise

    return backup


if __name__ == "__main__":

    async def main() -> None:
        url = "https://httpbin.org/anything"
        payload = {
            "library": {
                "ot": "whatever",
                "thing": "whatever",
            },
            "playlist_items": [
                {
                    "ot": "whatever",
                    "thing": "whatever",
                },
                {
                    "ot": "whatever",
                    "thing": "whatever",
                },
            ],
            "playlists": [
                {
                    "ot": "whatever",
                    "thing": "whatever",
                },
                {
                    "ot": "whatever",
                    "thing": "whatever",
                },
            ],
        }

        musi_uuid = uuid.uuid4()

        boundary_str = f"Boundary+Musi{musi_uuid}"
        boundary = f"--{boundary_str}".encode()

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary_str};",
            "User-Agent": "Musi/25691 CFNetwork/1206 Darwin/20.1.0",
        }

        # hack because httpx doesn't appear to support custom boundaries like requests does.
        content = (
            boundary
            + b"\n"
            + b'Content-Disposition: form-data; name="data"'
            + b"\n\n"
            + json.dumps(payload).encode()
            + b"\n"
            + boundary
            + b"\n"
            + b'Content-Disposition: form-data; name="uuid"'
            + b"\n\n"
            + str(musi_uuid).encode()
            + b"\n"
            + boundary
            + b"--\n"
        )

        async with httpx.AsyncClient(headers=headers) as client:
            response2 = await client.post(url, content=content)

    asyncio.run(main())
