import asyncio
import json
import typing as t
import uuid

import httpx
import requests
from requests_toolbelt import MultipartEncoder
import rich

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
    musi_library: MusiLibrary,
    musi_playlists: t.Iterable[MusiPlaylist],
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
        "data": {
            "library": musi_library_dict,
            "playlist_items": musi_video_dicts,
            "playlists": musi_playlist_dicts,
        },
        "uuid": str(musi_uuid),
    }

    # multipart_encoder = MultipartEncoder(
    #     fields={"data": json.dumps(payload), "uuid": str(musi_uuid)},
    #     boundary=f"Boundary+Musi{musi_uuid}",
    # )
    # headers = {
    #     "Content-Type": multipart_encoder.content_type,
    #     "User-Agent": "Musi/25691 CFNetwork/1206 Darwin/20.1.0",
    # }
    # resp = requests.post(
    #     "https://feelthemusi.com/api/v4/backups/create", data=multipart_encoder, headers=headers  # type: ignore
    # )

    # rich.print(payload)

    headers = {
        "User-Agent": "Musi/25691 CFNetwork/1206 Darwin/20.1.0",
    }

    async with httpx.AsyncClient() as client:
        url = "https://feelthemusi.com/api/v4/backups/create"
        resp = await client.post(url, data=payload, headers=headers)

    rich.print(resp.text)

    backup = MusiResponse(**resp.json())
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

        tracks_uuid = uuid.uuid4()
        multipart_encoder = MultipartEncoder(
            fields={"data": json.dumps(payload), "uuid": str(tracks_uuid)},
            boundary=f"Boundary+Musi{tracks_uuid}",
        )
        headers = {
            "Content-Type": multipart_encoder.content_type,
            "User-Agent": "Musi/25691 CFNetwork/1206 Darwin/20.1.0",
        }

        async with httpx.AsyncClient(headers=headers) as client:
            response1 = await client.post(url, data={"data": json.dumps(payload), "uuid": str(tracks_uuid)})

        response2 = requests.post(url, data=multipart_encoder, headers=headers)  # type: ignore

        rich.print(response1.json())
        rich.print(response2.json())

    asyncio.run(main())
