from __future__ import annotations

import typing as t
from dataclasses import field

from pydantic.dataclasses import dataclass

from spotify_to_musi.commons import remove_features_from_title, remove_parens
from spotify_to_musi.exceptions import EmptyTupleError


@dataclass(frozen=True)
class Artist:
    name: str


@dataclass(frozen=True)
class Track:
    name: str
    duration: int
    artists: tuple[Artist, ...]
    # there can be a song on multiple albums, ie. original, deluxe, etc.
    album_name: t.Optional[str] = field(compare=False)
    is_explicit: bool = field(compare=False)

    def __post_init__(self: Track) -> None:
        if not self.artists:
            raise EmptyTupleError("artists")

    @property
    def primary_artist(self: Track) -> Artist:
        return self.artists[0]

    @property
    def secondary_artists(self: Track) -> tuple[Artist, ...] | None:
        return self.artists[1:] or None

    @property
    def featuring_text(self: Track) -> str:
        # sourcery skip: assign-if-exp, reintroduce-else, swap-if-expression
        if not self.secondary_artists:
            return ""
        return f" (feat. {' & '.join(a.name for a in self.secondary_artists)})"

    # maybe cache this?
    @property
    def name_with_features(self: Track) -> str:
        """
        Remove parens and features from title (if they exist)
        and add features to title.
        If an artist doesn't list their features in the title themselves,
        it's better to add it for improved search results.
        """
        name = self.name
        name = remove_parens(name)
        name = remove_features_from_title(name)
        return self.name

    @property
    def query(self: Track) -> str:
        base_query = f"{self.primary_artist.name} - {self.name_with_features}"
        base_query += self.featuring_text
        return base_query

    @property
    def colorized_query(self: Track) -> str:
        """
        Colorized query used w/ rich lib for printing
        """
        return (
            f"[bold white]{self.primary_artist.name}[/bold white] - [grey53]{self.name}{self.featuring_text}[/grey53]"
        )


@dataclass(frozen=True)
class Playlist:
    id: str
    name: str = field(compare=False)
    cover_image_url: t.Optional[str] = field(repr=False, compare=False)
    tracks: tuple[Track, ...] = field(repr=False, compare=False)
