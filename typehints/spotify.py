from __future__ import annotations

from typing import Optional, TypedDict


# --- both --- #

class SpotifyExternalUrls(TypedDict):
    spotify: str


class SpotifyImage(TypedDict):
    height: int
    url: str
    width: int


# --- current user playlists --- #


class Owner(TypedDict):
    display_name: str
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    type: str
    uri: str


class Tracks(TypedDict):
    href: str
    total: int


class CurrentUserPlaylists(TypedDict):
    collaborative: bool
    description: str
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    images: list[SpotifyImage]
    name: str
    owner: Owner
    primary_color: None
    public: bool
    snapshot_id: str
    tracks: Tracks
    type: str
    uri: str


# --- playlist items --- #


class AddedBy(TypedDict):
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    type: str
    uri: str


class Artist(TypedDict):
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    name: str
    type: str
    uri: str


class Album(TypedDict):
    album_type: str
    artists: list[Artist]
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    images: list[SpotifyImage]
    name: str
    release_date: str
    release_date_precision: str
    total_tracks: int
    type: str
    uri: str


class ExternalIds(TypedDict):
    isrc: str


class SpotifyTrack(TypedDict):
    album: Album
    artists: list[Artist]
    disc_number: int
    duration_ms: int
    episode: bool
    explicit: bool
    external_ids: ExternalIds
    external_urls: SpotifyExternalUrls
    href: str
    id: str
    is_local: bool
    name: str
    popularity: int
    preview_url: Optional[str]
    track: bool
    track_number: int
    type: str
    uri: str


class VideoThumbnail(TypedDict):
    url: None


class SpotifyPlaylistItem(TypedDict):
    added_at: str
    added_by: AddedBy
    is_local: bool
    primary_color: None
    track: SpotifyTrack
    video_thumbnail: VideoThumbnail
