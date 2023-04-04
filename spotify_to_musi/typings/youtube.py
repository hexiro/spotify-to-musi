from __future__ import annotations

from typing import TypedDict


class Album(TypedDict):
    name: str
    id: str | None


class Artist(TypedDict):
    name: str
    id: str | None


class FeedbackTokens(TypedDict):
    add: None
    remove: None


class Thumbnail(TypedDict):
    url: str
    width: int
    height: int


# not all these fields always exist, but they will on a song
class YoutubeMusicSearch(TypedDict):
    category: str
    resultType: str
    videoId: str
    title: str
    views: str  # only on videos
    artists: list[Artist]
    album: Album
    duration: str
    duration_seconds: int
    isExplicit: bool  # only on videos
    feedbackTokens: FeedbackTokens
    videoType: str
    year: None
    thumbnails: list[Thumbnail]
