from __future__ import annotations

import httpx
import pytest
import rich

import typing as t

from spotify_to_musi import ytmusic
from spotify_to_musi.typings.core import Artist, Track
from spotify_to_musi.youtube import (youtube_music_search_options,
                                     youtube_result_score)

if t.TYPE_CHECKING:
    from spotify_to_musi.typings.youtube import YouTubeMusicResult


pytest_plugins = ("pytest_asyncio",)


track_to_expected_video_ids: list[tuple[Track, list[str]]] = [
    (
        Track(
            name="Demon Time (feat. Ski Mask The Slump God)",
            artists=(
                Artist(name="Trippie Redd"),
                Artist(name="Ski Mask The Slump God"),
            ),
            duration=159,
            album_name="Trip At Knight (Complete Edition)",
            is_explicit=True,
        ),
        ["uoyaDo9B5Eo"],
    ),
    # b/c doja cat songs might come up
    (
        Track(
            name="Doja",
            artists=(Artist(name="$NOT"), Artist(name="A$AP Rocky")),
            duration=171,
            album_name="Ethereal",
            is_explicit=True,
        ),
        ["s477U69XPlA", "lxfljkiR5Xc"],
    ),
    # b/c same mixtape has a song with same duration (1 second difference)
    (
        Track(
            name="Do What I Want",
            artists=(Artist(name="Lil Uzi Vert"),),
            duration=175,
            album_name="The Perfect LUV Tape",
            is_explicit=True,
        ),
        ["ra1cvbdYhps"],
    ),
    (
        Track(
            name="Erase Your Social",
            artists=(Artist(name="Lil Uzi Vert"),),
            duration=199,
            album_name="The Perfect LUV Tape",
            is_explicit=True,
        ),
        ["X21M7w6IkoM"],
    ),
    # b/c doesn't have 'song' on youtube music
    (
        Track(
            name="How Did I Get Here (feat. J. Cole)",
            artists=(Artist(name="Offset"), Artist(name="J. Cole")),
            duration=276,
            album_name="FATHER OF 4",
            is_explicit=True,
        ),
        ["v8PRzHXYcII"],
    ),
    # b/c has multiple official uploads on youtube music
    (
        Track(
            name="ORANGE SODA",
            artists=(Artist(name="Baby Keem"),),
            duration=129,
            album_name="DIE FOR MY BITCH",
            is_explicit=True,
        ),
        ["PTv7cJjNig8"],
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("track,expected_video_ids", track_to_expected_video_ids)
async def test_transfer(track: Track, expected_video_ids: list[str]) -> None:
    options: list[YouTubeMusicResult] = []

    async with httpx.AsyncClient() as client:
        youtube_music_search = await ytmusic.search_music(track.query, client)

    assert youtube_music_search is not None

    options = youtube_music_search_options(track, youtube_music_search)
    best_option = options[0]

    rich.print(track.query)
    rich.print([(option, youtube_result_score(option, track)) for option in options])

    assert best_option.video_id in expected_video_ids
