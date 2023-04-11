from __future__ import annotations
import time


from pydantic import BaseModel, Field
import typing as t

from typings.core import Track
from typings.youtube import YouTubeTrack


class MusiTrack(YouTubeTrack):
    created_date: float = Field(default_factory=lambda: time.time())

    def musi_item(self, index: int) -> MusiItem:
        return MusiItem(
            video_id=self.video_id,
            pos=index,
            cd=int(self.created_date),
        )

    def musi_video(self) -> MusiVideo:
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
    ciu: str  # playlist cover image (url)


class MusiPlaylist(BaseModel):
    name: str
    tracks: tuple[MusiTrack, ...] = Field(exclude=True)
    # items: list[MusiItem]
    ciu: str = Field(alias="cover_image_url")
    date: int = Field(default_factory=lambda: int(time.time()))
    ot: t.Literal["custom"] = Field(default="custom", const=True)
    type: t.Literal["user"] = Field(default="user", const=True)

    def dict(self, **kwargs) -> MusiPlaylistDict:
        items: list[MusiItemDict] = [track.musi_item(index).dict() for index, track in enumerate(self.tracks)]  # type: ignore
        super_dict = super().dict(**kwargs)
        return {
            "ot": super_dict["ot"],
            "items": items,
            "name": super_dict["name"],
            "type": super_dict["type"],
            "date": super_dict["date"],
            "ciu": super_dict["ciu"],
        }


class MusiLibraryDict(t.TypedDict):
    ot: t.Literal["custom"]
    items: list[MusiItemDict]
    name: t.Literal["My Library"]
    date: int  # int(time.time())


class MusiLibrary(BaseModel):
    tracks: tuple[MusiTrack, ...] = Field(exclude=True)
    # items: list[MusiItem]
    ot: t.Literal["custom"] = Field(default="custom", const=True)
    name: t.Literal["My Library"] = Field(default="My Library", const=True)
    date: int = Field(default_factory=lambda: int(time.time()))

    def dict(self, **kwargs) -> MusiLibraryDict:
        items: list[MusiItemDict] = [track.musi_item(index).dict() for index, track in enumerate(self.tracks)]  # type: ignore
        super_dict = super().dict(**kwargs)
        return {"ot": super_dict["ot"], "items": items, "name": super_dict["name"], "date": super_dict["date"]}


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
