from __future__ import annotations


from pydantic import BaseModel, Field, validator
from pydantic.dataclasses import dataclass
from dataclasses import field

from commons import remove_features_from_title, remove_parens


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

    @validator("name")
    def validate_name(cls, v: str) -> str:
        """
        Remove parens and features from title
        (will be added back in the query)
        """
        v = remove_parens(v)
        v = remove_features_from_title(v)
        return v

    @validator("artists")
    def validate_artists(cls, v: tuple) -> tuple:
        return validate_tuple_isnt_empty(v)

    @property
    def primary_artist(self) -> Artist:
        return self.artists[0]

    @property
    def secondary_artists(self) -> tuple[Artist, ...]:
        return self.artists[1:]

    @property
    def featuring_text(self) -> str:
        if self.secondary_artists:
            return f" (feat. {' & '.join(a.name for a in self.secondary_artists)})"
        return ""

    @property
    def query(self) -> str:
        base_query = f"{self.primary_artist.name} - {self.name}"
        base_query += self.featuring_text
        return base_query

    @property
    def colorized_query(self) -> str:
        """
        Colorized query used w/ rich lib for printing
        """
        return f"[bold white]{self.primary_artist.name}[/bold white] - [grey53]{self.name}{self.featuring_text}[/grey53]"


@dataclass
class Playlist:
    id: str
    name: str = field(compare=False)
    track_count: int = field(init=False, compare=False)
    cover_image_url: str | None = field(repr=False, compare=False)
    tracks: tuple[Track, ...] = field(repr=False, compare=False)

    def __post_init__(self):
        self.track_count = len(self.tracks)


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
