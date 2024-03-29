from __future__ import annotations

import typing as t
from dataclasses import field

from pydantic import BaseModel, field_validator
from pydantic.dataclasses import dataclass

from spotify_to_musi.typings.core import Artist, Playlist, Track


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
    album: t.Optional[YouTubeMusicAlbum]
    is_explicit: bool

    @field_validator("name", check_fields=False)  # type: ignore[type-var]
    @classmethod
    def must_not_be_single(cls, v: YouTubeMusicAlbum, values: dict[str, t.Any]) -> YouTubeMusicAlbum | None:
        # sourcery skip: assign-if-exp, reintroduce-else
        if v.name == values["title"]:
            return None

        return v


class YouTubeMusicVideo(_YouTubeMusicResultType):
    views: int


YouTubeMusicResult = t.Union[YouTubeMusicSong, YouTubeMusicVideo]


class YouTubeMusicSearch(BaseModel):
    top_result: t.Optional[YouTubeMusicResult]
    songs: list[YouTubeMusicSong]
    videos: list[YouTubeMusicVideo]


@dataclass(frozen=True)
class YouTubeTrack(Track):
    youtube_name: str
    youtube_duration: int
    youtube_artists: tuple[Artist, ...]
    is_explicit: t.Optional[bool]  # type: ignore[assignment]
    video_id: str


@dataclass(frozen=True)
class YouTubePlaylist(Playlist):
    tracks: tuple[YouTubeTrack, ...] = field(repr=False, compare=False)
