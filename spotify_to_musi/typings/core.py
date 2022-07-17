from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple, TypedDict


if TYPE_CHECKING:
    from typing import TypeAlias
    from typings.musi import MusiVideo, MusiItem


@dataclass(eq=True)
class Playlist:
    name: str
    id: str
    cover_url: str
    tracks: list[Track] = field(default_factory=list, init=False, repr=False, compare=False)

    def remove_unloaded_tracks(self) -> None:
        self.tracks = [track for track in self.tracks if track.loaded]

    def to_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "cover_url": self.cover_url,
            "tracks": [track.to_dict() for track in self.tracks],
        }


# youtube video and data about the spotify artist that was used to find it.


class TrackDict(TypedDict):
    artist: str
    song: str
    duration: int  # in seconds
    video_id: str


@dataclass(unsafe_hash=True)
class Track:
    artist: str
    song: str
    spotify_duration: int = field(default=-1, compare=False)
    duration: int = field(default=-1, hash=False, compare=False)  # in seconds
    video_id: str | None = field(default=None, hash=False, compare=False)
    creation_time: float = field(default=-1, hash=False, compare=False)

    def __post_init__(self):
        self.creation_time = time.time()

    @property
    def title(self) -> str:
        return f"{self.artist} - {self.song}"

    @property
    def loaded(self) -> bool:
        return self.duration != -1 and self.video_id is not None

    def to_dict(self) -> TrackDict:
        if self.duration == -1 or self.video_id is None:  # if i try and DRY then pylance yells
            raise Exception("data must be loaded to call this")
        return {
            "artist": self.artist,
            "song": self.song,
            "duration": self.duration,
            "video_id": self.video_id,
        }

    def to_musi_video(self) -> MusiVideo:
        if self.duration == -1 or self.video_id is None:
            raise Exception("data must be loaded to call this")
        return {
            "created_date": self.creation_time,
            "video_duration": self.duration,
            "video_name": self.song,
            "video_creator": self.artist,
            "video_id": self.video_id,
        }

    def to_musi_item(self, position: int) -> MusiItem:
        if self.duration == -1 or self.video_id is None:
            raise Exception("data must be loaded to call this")
        return {
            "cd": int(self.creation_time),
            "pos": position,
            "video_id": self.video_id,
        }


class TrackData(NamedTuple):
    duration: int
    video_id: str


LikedSongs: TypeAlias = list[Track]
