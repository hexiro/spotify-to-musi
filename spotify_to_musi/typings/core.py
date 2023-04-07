from __future__ import annotations


from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass
from dataclasses import field


class Artist(BaseModel):
    name: str


class Track(BaseModel):
    name: str
    duration: int
    artists: list[Artist] = Field(min_items=1)

    @property
    def query(self) -> str:
        return f"{self.artists[0].name} - {self.name}"


@dataclass
class Playlist:
    name: str = field(compare=False)
    id: str
    cover_image_url: str = field(compare=False)
    tracks: list[Track] = field(default_factory=list, repr=True, compare=False)


if __name__ == "__main__":
    pl1 = Playlist(
        name="test",
        id="test",
        cover_image_url="test",
        tracks=[
            Track(
                name="test",
                duration=100,
                artists=[Artist(name="test")],
            ),
        ],
    )

    pl2 = Playlist(
        name="test",
        id="test",
        cover_image_url="test",
        tracks=[],
    )

    print(pl1 == pl2)
