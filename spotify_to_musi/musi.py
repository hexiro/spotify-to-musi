import hashlib
import json
import typing as t
import uuid

import httpx
import rich

import pydantic.json
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


def convert_from_youtube(
    youtube_playlists: t.Iterable[YouTubePlaylist], youtube_liked_tracks: t.Iterable[YouTubeTrack]
) -> tuple[tuple[MusiPlaylist, ...], MusiLibrary]:
    musi_playlists = convert_playlists_to_musi_playlists(youtube_playlists)
    musi_library = covert_youtube_tracks_to_musi_library(youtube_liked_tracks)

    return musi_playlists, musi_library


def covert_youtube_tracks_to_musi_tracks(youtube_tracks: t.Iterable[YouTubeTrack]) -> tuple[MusiTrack, ...]:
    musi_tracks: list[MusiTrack] = []

    for youtube_track in youtube_tracks:
        # a little verbose
        musi_track = MusiTrack(
            name=youtube_track.name,
            duration=youtube_track.duration,
            artists=youtube_track.artists,
            album_name=youtube_track.album_name,
            is_explicit=youtube_track.is_explicit,
            youtube_name=youtube_track.youtube_name,
            youtube_duration=youtube_track.youtube_duration,
            youtube_artists=youtube_track.youtube_artists,
            video_id=youtube_track.video_id,
        )
        musi_tracks.append(musi_track)

    return tuple(musi_tracks)


def covert_youtube_tracks_to_musi_library(youtube_tracks: t.Iterable[YouTubeTrack]) -> MusiLibrary:
    musi_tracks = covert_youtube_tracks_to_musi_tracks(youtube_tracks)
    return MusiLibrary(tracks=musi_tracks)


def convert_playlists_to_musi_playlists(youtube_playlists: t.Iterable[YouTubePlaylist]) -> tuple[MusiPlaylist, ...]:
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


def generate_musi_uuid(musi_videos: list[MusiVideo]) -> uuid.UUID:
    """
    Generate a deterministic UUID based on the video IDs of the provided MusiVideo-s.
    """
    video_ids: set[str] = set()

    for musi_video in musi_videos:
        if musi_video.video_id in video_ids:
            continue
        video_ids.add(musi_video.video_id)

    video_ids_json = json.dumps(sorted(video_ids), default=pydantic.json.pydantic_encoder)
    video_ids_json_bytes = video_ids_json.encode("utf-8")

    video_ids_hash = hashlib.md5(video_ids_json_bytes)
    hexdigest = video_ids_hash.hexdigest()

    return uuid.uuid3(uuid.NAMESPACE_OID, hexdigest)


async def upload_to_musi(
    musi_playlists: t.Iterable[MusiPlaylist],
    musi_library: MusiLibrary,
) -> MusiResponse:
    musi_videos: list[MusiVideo] = []

    for musi_track in musi_library.tracks:
        try:
            musi_videos.append(musi_track.musi_video())
        except pydantic.error_wrappers.ValidationError as exc:
            rich.print(f"[red]validation error:[/red] {musi_track!r}")
            raise exc
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

    musi_uuid = generate_musi_uuid(musi_videos)
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

    try:
        backup = MusiResponse(**resp.json())
    except (pydantic.error_wrappers.ValidationError, json.decoder.JSONDecodeError):
        rich.print(f"[bold red]ERROR:[/bold red] {resp.text}]")
        raise

    return backup
