from __future__ import annotations

from typing import TypedDict


# --- all --- #


class SpotifyExternalUrls(TypedDict):
    spotify: str


class SpotifyImage(TypedDict):
    height: int
    url: str
    width: int


class SpotifyArtist(TypedDict):
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    name: str
    type: str
    uri: str


class SpotifyAlbum(TypedDict):
    album_type: str | None
    artists: list[SpotifyArtist]
    external_urls: SpotifyExternalUrls
    href: str | None
    id: str | None
    images: list[SpotifyImage]
    name: str | None
    release_date: str | None
    release_date_precision: str | None
    total_tracks: int  # might not exist if is_local?
    type: str
    uri: str | None


class SpotifyTrack(TypedDict):
    album: SpotifyAlbum
    artists: list[SpotifyArtist]
    disc_number: int
    duration_ms: int
    episode: bool  # might not exist always?
    explicit: bool
    external_ids: SpotifyExternalIds
    external_urls: SpotifyExternalUrls
    href: str | None
    id: str | None
    is_local: bool
    name: str
    popularity: int
    preview_url: str | None
    track: bool  # might not exist if is_local?
    track_number: int
    type: str
    uri: str


# --- current user playlists --- #


class SpotifyPlaylistOwner(TypedDict):
    display_name: str
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    type: str
    uri: str


class SpotifyPlaylistTracks(TypedDict):
    href: str
    total: int


class SpotifyPlaylist(TypedDict):
    collaborative: bool
    description: str
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    images: list[SpotifyImage]
    name: str
    owner: SpotifyPlaylistOwner
    primary_color: None
    public: bool
    snapshot_id: str
    tracks: SpotifyPlaylistTracks
    type: str
    uri: str


# --- playlist items --- #


class SpotifyPlaylistAddedBy(TypedDict):
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    type: str
    uri: str


class SpotifyExternalIds(TypedDict):
    isrc: str


class SpotifyVideoThumbnail(TypedDict):
    url: str | None


class SpotifyPlaylistItem(TypedDict):
    added_at: str
    added_by: SpotifyPlaylistAddedBy
    is_local: bool
    primary_color: None
    track: SpotifyTrack | None
    video_thumbnail: SpotifyVideoThumbnail


# --- liked songs --- #


class SpotifyArtistsItem(TypedDict):
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    name: str
    type: str
    uri: str


class SpotifyLikedSong(TypedDict):
    added_at: str
    track: SpotifyTrack
