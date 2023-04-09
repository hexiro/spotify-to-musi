from __future__ import annotations


from pydantic import BaseModel, Field, validator
from pydantic.dataclasses import dataclass
from dataclasses import field


def validate_tuple_isnt_empty(value: tuple) -> tuple:
    if len(value) == 0:
        raise ValueError("Tuple can't be empty")
    return value


class Artist(BaseModel):
    name: str


class Track(BaseModel):
    name: str
    duration: int
    artists: tuple[Artist, ...]
    album_name: str | None
    is_explicit: bool

    @validator("artists")
    def validate_artists(cls, v: tuple) -> tuple:
        return validate_tuple_isnt_empty(v)

    @property
    def query(self) -> str:
        return f"{self.artists[0].name} - {self.name}"

    @property
    def colorized_query(self) -> str:
        """
        Colorized query used w/ rich lib for printing
        """
        return f"[bold white]{self.artists[0].name}[/bold white] - [gray]{self.name}[/gray]"


@dataclass
class Playlist:
    name: str = field(compare=False)
    track_count: int = field(init=False, compare=False)
    id: str
    cover_image_url: str = field(repr=False, compare=False)
    tracks: tuple[Track, ...] = field(repr=False, compare=False)

    def __post_init__(self):
        self.track_count = len(self.tracks)
        validate_tuple_isnt_empty(self.tracks)


if __name__ == "__main__":
    pl1 = Playlist(
        name="test",
        id="test",
        cover_image_url="test",
        tracks=(
            Track(
                name="test",
                duration=100,
                artists=(Artist(name="test"),),
                album_name="test",
                is_explicit=False,
            ),
            Track(
                name="test2",
                duration=100,
                artists=(Artist(name="test2"),),
                album_name="test2",
                is_explicit=False,
            ),
        ),
    )
    try:
        pl2 = Playlist(
            name="test",
            id="test",
            cover_image_url="test",
            tracks=tuple(),
        )
    except ValueError as e:
        print("Expected Error:", e)
    else:
        raise Exception("Expected ValueError")

    track1 = Track(
        name="test",
        duration=100,
        artists=(Artist(name="test"),),
        album_name="test",
        is_explicit=False,
    )

    track2 = Track(
        name="test",
        duration=100,
        artists=tuple(),
        album_name="test",
        is_explicit=False,
    )
