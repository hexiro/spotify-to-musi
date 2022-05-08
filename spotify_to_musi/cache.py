from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, TypedDict, Iterable


from .paths import spotify_data_path, data_cache_path
from .typings.core import Track

if TYPE_CHECKING:
    from .typings.core import TrackDict


def get_cached_tracks() -> list[Track]:
    tracks: list[Track] = []
    if data_cache_path.is_file():
        try:
            with open(data_cache_path) as file:
                cached_data: list[TrackDict] = json.load(file)
            for track in cached_data:
                deserialized = Track(**track)
                tracks.append(deserialized)
        except json.JSONDecodeError:
            pass
    return tracks


def cache_tracks(tracks: Iterable[Track]) -> None:
    cache_items: list[TrackDict] = []
    for track in tracks:
        if not track.loaded:
            continue
        track_dict = track.to_dict()
        cache_items.append(track_dict)
    with open(data_cache_path, "w") as file:
        json.dump(cache_items, file, indent=4)


class SpotifySecrets(TypedDict):
    spotify_client_id: str
    spotify_client_secret: str


def store_spotify_secrets(spotify_client_id: str, spotify_client_secret: str) -> None:
    """Store Spotify secrets to fs"""
    data: SpotifySecrets = {
        "spotify_client_id": spotify_client_id,
        "spotify_client_secret": spotify_client_secret,
    }
    with open(spotify_data_path, "w") as file:
        json.dump(data, file)


def patch_spotify_secrets() -> None:
    with open(spotify_data_path, "r") as file:
        data: SpotifySecrets = json.load(file)
    os.environ["SPOTIPY_CLIENT_ID"] = data["spotify_client_id"]
    os.environ["SPOTIPY_CLIENT_SECRET"] = data["spotify_client_secret"]
