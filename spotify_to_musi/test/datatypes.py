import rich
from pydantic import BaseModel, validator
import typing as t


def duration_in_seconds(duration_str: str) -> int:
    """
    Converts a duration string to seconds.
    Example: '2:30' -> 150
    """
    if not duration_str:
        return 0

    split = duration_str.split(":")
    split.reverse()

    multipliers = [1, 60, 3600, 3600 * 24]
    duration = 0

    for i, part in enumerate(split):
        duration += int(part) * multipliers[i]

    return duration


class YouTubeMusicArtist(BaseModel):
    name: str
    id: str


class YouTubeMusicAlbum(BaseModel):
    name: str


class _YouTubeMusicResultType(BaseModel):
    title: str
    artists: list[YouTubeMusicArtist]
    duration: int
    video_id: str


class YouTubeMusicSong(_YouTubeMusicResultType):
    album: YouTubeMusicAlbum
    is_explicit: bool


class YouTubeMusicVideo(_YouTubeMusicResultType):
    views: int


TopResult: t.TypeAlias = YouTubeMusicSong | YouTubeMusicVideo | None


class YoutubeMusicSearch(BaseModel):
    top_result: YouTubeMusicSong | YouTubeMusicVideo | None
    songs: list[YouTubeMusicSong]
    videos: list[YouTubeMusicVideo]


if __name__ == "__main__":
    song = YouTubeMusicSong(
        title="Crushin'",
        artists=[YouTubeMusicArtist(name="4me", id="123")],
        album=YouTubeMusicAlbum(name="Crushin'"),
        duration=duration_in_seconds("3:09"),
        is_explicit=True,
        video_id="7ydCpvVe85k",
    )

    rich.print(song)
    # rich.print(song.__annotations__)
