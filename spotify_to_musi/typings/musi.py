from __future__ import annotations

import time
import typing as t
from dataclasses import field

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

from spotify_to_musi.typings.core import (  # weird pydantic case where this has to be imported # noqa: F401
    Artist,
)
from spotify_to_musi.typings.youtube import YouTubeTrack

if t.TYPE_CHECKING:
    import sys

    if sys.version_info <= (3, 10):
        from typing_extensions import NotRequired
    else:
        from typing import NotRequired


@dataclass(frozen=True)
class MusiTrack(YouTubeTrack):
    created_date: float = field(default_factory=time.time)

    def musi_item(self: MusiTrack, index: int) -> MusiItem:
        return MusiItem(
            video_id=self.video_id,
            pos=index,
            cd=int(self.created_date),
        )

    def musi_video(self: MusiTrack) -> MusiVideo:
        return MusiVideo(
            video_id=self.video_id,
            video_name=self.name,
            video_creator=self.artists[0].name,
            video_duration=self.youtube_duration,
            created_date=self.created_date,
        )


class MusiItemDict(t.TypedDict):
    cd: int  # int(time.time())
    pos: int  # index
    video_id: str


class MusiItem(BaseModel):
    cd: int = Field(default_factory=lambda: int(time.time()))
    pos: int
    video_id: str


class MusiPlaylistDict(t.TypedDict):
    ot: t.Literal["custom"]
    items: list[MusiItemDict]
    name: str
    type: t.Literal["user"]
    date: int  # int(time.time())
    ciu: NotRequired[str]  # playlist cover image (url)


class MusiPlaylist(BaseModel):
    name: str
    tracks: tuple[MusiTrack, ...] = Field(exclude=True)
    ciu: t.Optional[str] = Field(alias="cover_image_url")
    date: int = Field(default_factory=lambda: int(time.time()))
    ot: t.Literal["custom"] = Field(default="custom", const=True)
    type: t.Literal["user"] = Field(default="user", const=True)

    def dict(self: MusiPlaylist, **kwargs: t.Any) -> MusiPlaylistDict:  # type: ignore[override]
        items: list[MusiItemDict] = [track.musi_item(index).dict() for index, track in enumerate(self.tracks)]  # type: ignore
        super_dict = super().dict(**kwargs)
        data = {
            "ot": super_dict["ot"],
            "items": items,
            "name": super_dict["name"],
            "type": super_dict["type"],
            "date": super_dict["date"],
        }
        if self.ciu:
            data["ciu"] = super_dict["ciu"]
        return data  # type: ignore


class MusiLibraryDict(t.TypedDict):
    ot: t.Literal["custom"]
    items: list[MusiItemDict]
    name: t.Literal["My Library"]
    date: int  # int(time.time())


class MusiLibrary(BaseModel):
    tracks: tuple[MusiTrack, ...] = Field(exclude=True)
    ot: t.Literal["custom"] = Field(default="custom", const=True)
    name: t.Literal["My Library"] = Field(default="My Library", const=True)
    date: int = Field(default_factory=lambda: int(time.time()))

    def dict(self: MusiLibrary, **kwargs: t.Any) -> MusiLibraryDict:  # type: ignore[override]
        items: list[MusiItemDict] = [track.musi_item(index).dict() for index, track in enumerate(self.tracks)]  # type: ignore
        super_dict = super().dict(**kwargs)
        return {
            "ot": super_dict["ot"],
            "items": items,
            "name": super_dict["name"],
            "date": super_dict["date"],
        }


class MusiVideoDict(t.TypedDict):
    created_date: float  # time.time()
    video_duration: int  # in seconds
    video_name: str
    video_creator: str  # channel name
    video_id: str


class MusiVideo(BaseModel):
    video_id: str
    video_name: str
    video_creator: str
    video_duration: int
    created_date: float = Field(default_factory=time.time)


class MusiResponseDict(t.TypedDict):
    code: str
    diff: bool
    success: str  # message


class MusiResponse(BaseModel):
    code: str
    diff: bool
    success: str
