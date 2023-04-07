from __future__ import annotations

from pydantic import BaseModel


class SpotifyImage(BaseModel):
    url: str
    width: int | None
    height: int | None


class SpotifyPlaylistOwner(BaseModel):
    display_name: str
    href: str
    id: str
    type: str
    uri: str


class SpotifyBasicTrack(BaseModel):
    href: str
    total: int


class SpotifyPlaylist(BaseModel):
    name: str
    public: bool
    collaborative: bool
    id: str
    description: str
    href: str
    uri: str
    # type: t.Literal['playlist']
    # owner: SpotifyPlaylistOwner
    images: list[SpotifyImage]
    tracks: SpotifyBasicTrack

    @property
    def cover_image_url(self) -> str:
        return self.images[0].url

    @property
    def track_count(self) -> int:
        return self.tracks.total


### --- liked songs --- ###


class SpotifyArtist(BaseModel):
    href: str
    name: str
    id: str
    type: str
    uri: str


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
    # available_markets: Union[List, List[str]]
    # track_number: int
    # type: t.Literal['track']
    # uri: str
    # album: SpotifyAlbum
    # disc_number: int
    # external_ids: ExternalIds
    # external_urls: ExternalUrls
    # preview_url: Optional[str]

    @property
    def duration(self) -> int:
        return self.duration_ms // 1000
