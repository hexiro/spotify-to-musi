from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, TypeAlias

if TYPE_CHECKING:
    from typehints.musi import MusiVideo, MusiItem

# youtube video and data about the spotify artist that was used to find it.


class TrackDict(TypedDict):
    artist: str
    song: str
    duration: int  # in seconds
    video_id: str


@dataclass
class Track:
    artist: str
    song: str
    duration: int  # in seconds
    video_id: str
    is_from_cache: bool = False

    def __post_init__(self):
        self.creation_time = time.time()

    @property
    def title(self) -> str:
        return f"{self.artist} - {self.song}"

    def to_dict(self) -> TrackDict:
        return {
            "artist": self.artist,
            "song": self.song,
            "duration": self.duration,
            "video_id": self.video_id,
        }

    def to_musi_video(self) -> MusiVideo:
        return {
            "created_date": self.creation_time,
            "video_duration": self.duration,
            "video_name": self.song,
            "video_creator": self.artist,
            "video_id": self.video_id,
        }

    def to_musi_item(self, position: int) -> MusiItem:
        return {
            "cd": int(self.creation_time),
            "pos": position,
            "video_id": self.video_id,
        }
