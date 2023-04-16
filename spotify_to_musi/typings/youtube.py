from __future__ import annotations

import typing as t
from dataclasses import field

from pydantic import BaseModel, validator
from pydantic.dataclasses import dataclass
from typings.core import Artist, Playlist, Track


class YouTubeMusicArtist(BaseModel):
    name: str


class YouTubeMusicAlbum(BaseModel):
    name: str


class _YouTubeMusicResultType(BaseModel):
    title: str
    artists: tuple[YouTubeMusicArtist, ...]
    duration: int
    video_id: str


class YouTubeMusicSong(_YouTubeMusicResultType):
    album: YouTubeMusicAlbum | None
    is_explicit: bool

    @validator("album")
    def must_not_be_single(
        cls, v: YouTubeMusicAlbum, values: dict[str, t.Any]  # noqa: ANN101, N805
    ) -> YouTubeMusicAlbum | None:
        # sourcery skip: assign-if-exp, reintroduce-else
        if v.name == values["title"]:
            return None

        return v


class YouTubeMusicVideo(_YouTubeMusicResultType):
    views: int


YouTubeMusicResult = YouTubeMusicSong | YouTubeMusicVideo


class YouTubeMusicSearch(BaseModel):
    top_result: YouTubeMusicResult | None
    songs: list[YouTubeMusicSong]
    videos: list[YouTubeMusicVideo]


@dataclass(frozen=True)
class YouTubeTrack(Track):
    youtube_name: str
    youtube_duration: int
    youtube_artists: tuple[Artist, ...]
    is_explicit: bool | None
    video_id: str


@dataclass(frozen=True)
class YouTubePlaylist(Playlist):
    tracks: tuple[YouTubeTrack, ...] = field(repr=False, compare=False)


if __name__ == "__main__":
    from rich import print

    youtube_track = YouTubeTrack(
        name="test",
        duration=1,
        artists=(Artist(name="test"),),
        youtube_name="test",
        youtube_duration=1,
        youtube_artists=(Artist(name="test"),),
        album_name="test",
        is_explicit=True,
        video_id="test",
    )
    youtube_playlist = YouTubePlaylist(
        name="test",
        id="test",
        tracks=(youtube_track,),
        cover_image_url="test",
    )

    print({youtube_track})
