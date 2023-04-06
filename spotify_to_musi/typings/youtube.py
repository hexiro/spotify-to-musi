import typing as t
from pydantic import BaseModel, validator


class YouTubeMusicArtist(BaseModel):
    name: str


class YouTubeMusicAlbum(BaseModel):
    name: str


class _YouTubeMusicResultType(BaseModel):
    title: str
    artists: list[YouTubeMusicArtist]
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


YouTubeTopResult: t.TypeAlias = YouTubeMusicSong | YouTubeMusicVideo | None


class YoutubeMusicSearch(BaseModel):
    top_result: YouTubeMusicSong | YouTubeMusicVideo | None
    songs: list[YouTubeMusicSong]
    videos: list[YouTubeMusicVideo]
