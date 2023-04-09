import typing as t

from typings.core import Playlist, Track, Artist

from pydantic import BaseModel, validator
from pydantic.dataclasses import dataclass
from dataclasses import field


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
    youtube_name: str
    youtube_duration: int
    youtube_artists: tuple[Artist, ...]
    is_explicit: bool | None
    video_id: str


@dataclass
class YouTubePlaylist(Playlist):
    tracks: tuple[YouTubeTrack, ...] = field(repr=False, compare=False)


if __name__ == "__main__":
    youtube_playlist = YouTubePlaylist(
        name="test",
        id="test",
        tracks=tuple(),
        cover_image_url="test",
    )
