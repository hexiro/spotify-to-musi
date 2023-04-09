from __future__ import annotations
import time

import pydantic
from pydantic import BaseModel, Field
import typing as t


class MusiItemDict(t.TypedDict):
    cd: int  # int(time.time())
    pos: int  # index
    video_id: str


class MusiItem(BaseModel):
    video_id: str
    pos: int = Field(..., alias="index")
    cd: int = Field(default_factory=lambda: int(time.time()))


class MusiPlaylistDict(t.TypedDict):
    ot: t.Literal["custom"]
    items: list[MusiItemDict]
    name: str
    type: t.Literal["user"]
    date: int  # int(time.time())
    ciu: str  # playlist cover image (url)


class MusiPlaylist(BaseModel):
    name: str
    items: list[MusiItem] = Field(default_factory=list)
    ciu: str = Field(..., alias="cover_image_url")
    ot: t.Literal["custom"] = Field("custom", const=True)
    type: t.Literal["user"] = Field("user", const=True)
    date: int = Field(default_factory=lambda: int(time.time()))


class MusiLibraryDict(t.TypedDict):
    ot: t.Literal["custom"]
    items: list[MusiItemDict]
    name: t.Literal["My Library"]
    date: int  # int(time.time())


class MusiLibrary(BaseModel):
    items: list[MusiItem] = Field(default_factory=list)
    name: t.Literal["My Library"] = Field("My Library", const=True)
    ot: t.Literal["custom"] = Field("custom", const=True)
    date: int = Field(default_factory=lambda: int(time.time()))


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
