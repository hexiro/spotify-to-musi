import typing as t
from pydantic import BaseModel, validator

from typings.core import Track


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
    def must_not_be_single(cls, v: YouTubeMusicAlbum, values) -> YouTubeMusicAlbum | None:
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


class YouTubeTrack(Track):
    is_explicit: bool | None
    video_id: str
