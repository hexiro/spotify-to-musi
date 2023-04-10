from dataclasses import dataclass
import pytest
import rich


from spotify_to_musi import ytmusic
from spotify_to_musi.typings.core import Artist, Track
from spotify_to_musi.typings.youtube import YouTubeMusicResult
from spotify_to_musi.youtube import youtube_result_score

pytest_plugins = ("pytest_asyncio",)


track_to_expected_video_id: list[tuple[Track, str]] = [
    (
        Track(
            name="Demon Time (feat. Ski Mask The Slump God)",
            artists=(Artist(name="Trippie Redd"), Artist(name="Ski Mask The Slump God")),
            duration=159,
            album_name="Trip At Knight (Complete Edition)",
            is_explicit=True,
        ),
        "uoyaDo9B5Eo",
    ),
    (
        Track(
            name="Doja",
            artists=(Artist(name="$NOT"), Artist(name="A$AP Rocky")),
            duration=171,
            album_name="Ethereal",
            is_explicit=True,
        ),
        "s477U69XPlA",
    ),
    (
        Track(
            name="Do What I Want",
            artists=(Artist(name="Lil Uzi Vert"),),
            duration=175,
            album_name="The Perfect LUV Tape",
            is_explicit=True,
        ),
        "ra1cvbdYhps",
    ),
    (
        Track(
            name="Erase Your Social",
            artists=(Artist(name="Lil Uzi Vert"),),
            duration=199,
            album_name="The Perfect LUV Tape",
            is_explicit=True,
        ),
        "X21M7w6IkoM",
    ),
    (
        Track(
            name="How Did I Get Here (feat. J. Cole)",
            artists=(Artist(name="Offset"), Artist(name="J. Cole")),
            duration=276,
            album_name="FATHER OF 4",
            is_explicit=True,
        ),
        "v8PRzHXYcII",
    ),
    (
        Track(
            name="ORANGE SODA",
            artists=(Artist(name="Baby Keem"),),
            duration=129,
            album_name="DIE FOR MY BITCH",
            is_explicit=True,
        ),
        "PTv7cJjNig8",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("track,expected_video_id", track_to_expected_video_id)
async def test_transfer(track: Track, expected_video_id: str) -> None:
    options: list[YouTubeMusicResult] = []

    youtube_music_search = await ytmusic.search_music(track.query)
    assert youtube_music_search is not None

    if youtube_music_search.top_result:
        options.append(youtube_music_search.top_result)

    for youtube_music_song in youtube_music_search.songs:
        options.append(youtube_music_song)

    for youtube_music_video in youtube_music_search.videos:
        options.append(youtube_music_video)

    options.sort(key=lambda x: youtube_result_score(x, track), reverse=True)

    best_option = options[0]

    rich.print(track.query)
    rich.print([(option, youtube_result_score(option, track)) for option in options])

    assert best_option.video_id == expected_video_id
