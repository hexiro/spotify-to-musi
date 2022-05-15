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


class YoutubeMusicSearch(TypedDict):
    category: str
    resultType: str
    title: str
    album: Album
    feedbackTokens: FeedbackTokens
    videoId: str
    videoType: str
    duration: str
    year: None
    artists: list[Artist]
    duration_seconds: int
    isExplicit: bool
    thumbnails: list[Thumbnail]
