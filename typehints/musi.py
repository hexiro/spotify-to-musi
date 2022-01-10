from __future__ import annotations

from typing import TypedDict, Literal


class MusiItem(TypedDict):
    cd: int  # int(time.time())
    pos: int  # index
    video_id: str


class MusiPlaylist(TypedDict):
    ot: Literal["custom"]
    items: list[MusiItem]
    name: str
    type: Literal["user"]
    date: int  # int(time.time())


class MusiVideo(TypedDict):
    created_date: float  # time.time()
    video_duration: int  # in seconds
    video_name: str
    video_creator: str  # channel name
    video_id: str


class MusiBackupResponse(TypedDict):
    code: str
    diff: bool
    success: str  # message
