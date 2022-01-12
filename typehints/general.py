from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typehints.musi import MusiVideo, MusiItem


# youtube video and data about the spotify artist that was used to find it.

class DictSongAndVideo(TypedDict):
    spotify_artist: str
    spotify_name: str
    video_duration: int  # in seconds
    video_name: str
    video_creator: str  # channel name
    video_id: str


@dataclass
class SongAndVideo:
    spotify_artist: str
    spotify_name: str
    video_duration: int  # in seconds
    video_name: str
    video_creator: str  # channel name
    video_id: str
    is_from_cache: bool = False

    def __post_init__(self):
        self.created_date = time.time()

    @property
    def title(self) -> str:
        return f"{self.spotify_artist} - {self.spotify_name}"

    def to_dict(self) -> DictSongAndVideo:
        return {
            "spotify_artist": self.spotify_artist,
            "spotify_name": self.spotify_name,
            "video_duration": self.video_duration,
            "video_name": self.video_name,
            "video_creator": self.video_creator,
            "video_id": self.video_id,
        }

    def to_musi_video(self) -> MusiVideo:
        return {
            "created_date": self.created_date,
            "video_duration": self.video_duration,
            "video_name": self.video_name,
            "video_creator": self.video_creator,
            "video_id": self.video_id,
        }

    def to_musi_item(self, position: int) -> MusiItem:
        return {
            "cd": int(self.created_date),
            "pos": position,
            "video_id": self.video_id,
        }
