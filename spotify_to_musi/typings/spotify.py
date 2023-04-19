from __future__ import annotations

import typing as t

from exceptions import BlankNameError
from pydantic import BaseModel, validator


class SpotifyResponse(t.TypedDict):
    href: str
    items: list[t.Any]  # potentially make this a generic in future
    limit: int
    next: t.Optional[str]
    offset: int
    previous: t.Optional[str] 
    total: int


class SpotifyImage(BaseModel):
    url: str
    width: t.Optional[int]
    height: t.Optional[int]


class SpotifyPlaylistOwner(BaseModel):
    display_name: str
    href: str
    id: str
    type: str
    uri: str


class SpotifyBasicTracks(BaseModel):
    href: str
    total: int


class BasicSpotifyPlaylist(BaseModel):
    name: str
    public: bool
    collaborative: bool
    id: str
    description: str
    href: str
    uri: str
    images: list[SpotifyImage]
    tracks: SpotifyBasicTracks
    # 'owner': SpotifyPlaylistOwner  noqa: ERA001
    # 'type': Literalplaylist noqa: ERA001


class SpotifyArtist(BaseModel):
    href: str
    name: str
    id: str
    type: str
    uri: str

    @validator("name")
    def validate_name(cls, v: str) -> str:  # noqa: ANN101, N805
        if not v:
            raise BlankNameError("artist")
        return v


class SpotifyAlbum(BaseModel):
    album_group: t.Union[t.Literal["single"], str]  # not sure what other options are
    album_type: t.Union[t.Literal["single"], str]  # not sure what other options are
    artists: list[SpotifyArtist]
    # 'external_urls': ExternalUrls  noqa: ERA001
    href: str
    id: str
    images: list[SpotifyImage]
    is_playable: bool
    name: str
    release_date: str
    release_date_precision: str
    total_tracks: int
    type: t.Union[t.Literal["album"], str]  # not sure what other options are
    uri: str

    @validator("name")
    def validate_name(cls, v: str) -> str:  # noqa: ANN101, N805
        if not v:
            raise BlankNameError("album")
        return v


class SpotifyTrack(BaseModel):
    name: str
    id: str
    duration_ms: int
    href: str
    popularity: int
    # reference: https://hexdocs.pm/spotify_web_api/Spotify.Tracks.html#t:popularity/0
    # The popularity of the track. The value will be between 0 and 100, with 100 being the most popular. The popularity of a track is a value between 0 and 100, with 100 being the most popular. The popularity is calculated by algorithm and is based, in the most part, on the total number of plays the track has had and how recent those plays are.
    explicit: bool
    is_local: bool = False
    artists: list[SpotifyArtist]
    # 'available_markets': Union[List, List[str]]   noqa: ERA001
    # 'track_number': int  noqa: ERA001
    # 'type': t.Literal['track']  noqa: ERA001
    # 'uri': str  noqa: ERA001
    album: SpotifyAlbum
    # 'disc_number': int  noqa: ERA001
    # 'external_ids': ExternalIds  noqa: ERA001
    # 'external_urls': ExternalUrls  noqa: ERA001
    # 'preview_url': Optional[str]  noqa: ERA001

    @validator("name")
    def validate_name(cls, v: str) -> str:  # noqa: ANN101, N805
        if not v:
            raise BlankNameError("track")
        return v

    @property
    def duration(self: SpotifyTrack) -> int:
        return self.duration_ms // 1000

    @property
    def album_name(self: SpotifyTrack) -> str | None:
        # song is a single and has the single name as the album name,
        # represent this as None internally because it's not really an album
        if (
            self.album.album_type == "single"
            or self.album.album_group == "single"
            or self.album.total_tracks == 1
        ):
            return None

        return self.album.name


class SpotifyPlaylist(BasicSpotifyPlaylist):
    tracks: list[SpotifyTrack]  # type: ignore[assignment]

    @property
    def cover_image_url(self: SpotifyPlaylist) -> str | None:
        # sourcery skip: assign-if-exp, reintroduce-else, swap-if-expression
        if not self.images:
            return None

        return self.images[0].url

    @property
    def track_count(self: SpotifyPlaylist) -> int:
        return len(self.tracks)
