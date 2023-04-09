import asyncio

import typing as t

import rich

import ytmusic
from typings.core import Playlist, Track, Artist
from typings.youtube import (
    YouTubePlaylist,
    YouTubeTrack,
    YouTubeMusicResult,
    YouTubeMusicArtist,
    YouTubeMusicSong,
    YouTubeMusicVideo,
)


def youtube_result_score(youtube_result: YouTubeMusicResult, track: Track) -> float:
    score = 0
    score += title_score(track.name, youtube_result.title)
    score += artists_score(track.artists, youtube_result.artists)
    score += duration_score(track.duration, youtube_result.duration)

    if isinstance(youtube_result, YouTubeMusicSong):
        youtube_album_name = youtube_result.album.name if youtube_result.album else None
        score += album_score(track.album_name, youtube_album_name)
        score += explicit_score(track.is_explicit, youtube_result.is_explicit)

    return score


def duration_score(real_duration: int, result_duration: int) -> float:
    diff = abs(real_duration - result_duration)
    diff = max(0, diff - 1)

    if diff == 0:
        return 1

    return 1 / diff


def title_score(real_title: str, result_title: str) -> float:
    real_title = real_title.lower()
    result_title = result_title.lower()

    if real_title == result_title:
        return 1
    if real_title in result_title:
        return 0.75
    if result_title in real_title:
        return 0.75
    return 0


def explicit_score(real_is_explicit: bool, result_is_explicit: bool) -> float:
    if real_is_explicit == result_is_explicit:
        return 1
    return 0


def artists_score(real_artists: tuple[Artist, ...], result_artists: tuple[YouTubeMusicArtist, ...]) -> float:
    real_artist_names = [a.name.lower() for a in real_artists]
    result_artist_names = [a.name.lower() for a in result_artists]

    if real_artist_names == result_artist_names:
        return 1

    for real_artist_name in real_artist_names:
        if real_artist_name in result_artist_names:
            return 0.75

    for result_artist_name in result_artist_names:
        if result_artist_name in real_artist_names:
            return 0.75

    return 0


def album_score(real_album_name: str | None, result_album_name: str | None) -> float:
    if real_album_name is None and result_album_name is None:
        return 0.5

    if real_album_name is None or result_album_name is None:
        return 0

    real_album_name = real_album_name.lower()
    result_album_name = result_album_name.lower()

    if real_album_name == result_album_name:
        return 1
    if real_album_name in result_album_name:
        return 0.75
    if result_album_name in real_album_name:
        return 0.75
    return 0


async def convert_track_to_youtube_track(track: Track) -> YouTubeTrack | None:
    youtube_music_search = await ytmusic.search_music(track.query)

    if not youtube_music_search:
        return None

    options: list[YouTubeMusicResult] = []

    if youtube_music_search.top_result:
        options.append(youtube_music_search.top_result)

    for youtube_music_song in youtube_music_search.songs:
        options.append(youtube_music_song)

    for youtube_music_video in youtube_music_search.videos:
        options.append(youtube_music_video)

    options.sort(key=lambda x: youtube_result_score(x, track), reverse=True)

    if not options:
        return None

    youtube_music_result = options[0]
    top_score = youtube_result_score(youtube_music_result, track)

    # value might need to be tweaked later
    if top_score < 1:
        rich.print(f"[bold yellow1]SKIPPING:[/bold yellow1] {track.colorized_query} ({round(top_score, 3)})")
        return None

    # rich.print(options)
    # rich.print(youtube_result_score(options[0], track))

    album_name: str | None = None
    is_explicit: bool | None = None
    if isinstance(youtube_music_result, YouTubeMusicSong):
        if youtube_music_result.album:
            album_name = youtube_music_result.album.name

        is_explicit = youtube_music_result.is_explicit

    return YouTubeTrack(
        name=youtube_music_result.title,
        duration=youtube_music_result.duration,
        artists=tuple(Artist(name=x.name) for x in youtube_music_result.artists),
        album_name=album_name,
        is_explicit=is_explicit,
        video_id=youtube_music_result.video_id,
    )


async def convert_tracks_to_youtube_tracks(tracks: t.Iterable[Track]) -> tuple[YouTubeTrack]:
    youtube_tracks_tasks: list[asyncio.Task[YouTubeTrack | None]] = []

    for track in tracks:
        coro = convert_track_to_youtube_track(track)
        task = asyncio.create_task(coro)
        youtube_tracks_tasks.append(task)

    youtube_tracks: list[YouTubeTrack | None] = await asyncio.gather(*youtube_tracks_tasks)  # type: ignore
    youtube_tracks: tuple[YouTubeTrack] = tuple(x for x in youtube_tracks if x is not None)

    return youtube_tracks


async def convert_playlist_to_youtube_playlist(playlist: Playlist) -> YouTubePlaylist:
    youtube_tracks = await convert_tracks_to_youtube_tracks(playlist.tracks)
    return YouTubePlaylist(
        name=playlist.name,
        tracks=youtube_tracks,
        id=playlist.id,
        cover_image_url=playlist.cover_image_url,
    )


async def convert_playlists_to_youtube_playlists(playlists: t.Iterable[Playlist]) -> tuple[YouTubePlaylist]:
    youtube_playlists_tasks: list[asyncio.Task[YouTubePlaylist]] = []

    for playlist in playlists:
        coro = convert_playlist_to_youtube_playlist(playlist)
        task = asyncio.create_task(coro)
        youtube_playlists_tasks.append(task)

    youtube_playlists: tuple[YouTubePlaylist] = await asyncio.gather(*youtube_playlists_tasks)  # type: ignore

    return youtube_playlists