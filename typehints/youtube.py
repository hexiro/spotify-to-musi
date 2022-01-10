from __future__ import annotations

from typing import TypedDict


class ViewCount(TypedDict):
    text: str
    short: str


class Thumbnail(TypedDict):
    url: str
    width: int
    height: int


class DescriptionSnippet(TypedDict, total=False):
    text: str
    bold: bool  # optional. defaults to false


class Channel(TypedDict):
    name: str
    id: str
    thumbnails: list[Thumbnail]
    link: str


class Accessibility(TypedDict):
    title: str
    duration: str


class YoutubeResult(TypedDict):
    type: str
    id: str
    title: str
    publishedTime: str
    duration: str
    viewCount: ViewCount
    thumbnails: list[Thumbnail]
    richThumbnail: Thumbnail
    descriptionSnippet: list[DescriptionSnippet]
    channel: Channel
    accessibility: Accessibility
    link: str
    shelfTitle: None
