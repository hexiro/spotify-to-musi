import asyncio
import typing as t

import httpx
import rich
import tracks_cache
import ytmusic
from commons import (loaded_message, remove_features_from_title, remove_parens,
                     skipping_message, task_description)
from rich.progress import Progress, TaskID
from typings.core import Artist, Playlist, Track
from typings.youtube import (YouTubeMusicArtist, YouTubeMusicResult,
                             YouTubeMusicSearch, YouTubeMusicSong,
                             YouTubePlaylist, YouTubeTrack)


async def query_youtube(
    playlists: tuple[Playlist, ...],
    liked_tracks: tuple[Track, ...],
    progress: Progress,
) -> tuple[tuple[YouTubePlaylist, ...], tuple[YouTubeTrack, ...]]:
    await tracks_cache.load_cached_youtube_tracks()
    await tracks_cache.load_cached_tracks_dict()
    await tracks_cache.load_cached_tracks()

    deduplicated_tracks: set[Track] = set(liked_tracks)
    for playlist in playlists:
        deduplicated_tracks.update(set(playlist.tracks))

    total = len(deduplicated_tracks)
    task_id = progress.add_task(
        task_description(querying="YouTube", color="red"), total=total
    )

    youtube_tracks = await fetch_youtube_tracks(deduplicated_tracks, progress, task_id)
    await tracks_cache.update_cached_tracks(youtube_tracks)

    youtube_liked_tracks = await convert_tracks_to_youtube_tracks(liked_tracks)
    if youtube_liked_tracks:
        rich.print(
            loaded_message(
                source="YouTube",
                loaded="Liked Songs",
                tracks_count=len(youtube_liked_tracks),
                color="red",
            )
        )

    youtube_playlists = await convert_playlists_to_youtube_playlists(playlists)
    for youtube_playlist in youtube_playlists:
        rich.print(
            loaded_message(
                source="YouTube",
                loaded="Playlist",
                name=youtube_playlist.name,
                color="red",
            )
        )

    return youtube_playlists, youtube_liked_tracks


async def convert_tracks_to_youtube_tracks(
    tracks: t.Iterable[Track],
) -> tuple[YouTubeTrack, ...]:
    return await tracks_cache.match_tracks_to_youtube_tracks(tracks)


async def convert_playlist_to_youtube_playlist(playlist: Playlist) -> YouTubePlaylist:
    youtube_tracks = await tracks_cache.match_tracks_to_youtube_tracks(playlist.tracks)
    youtube_playlist = YouTubePlaylist(
        name=playlist.name,
        tracks=youtube_tracks,
        id=playlist.id,
        cover_image_url=playlist.cover_image_url,
    )
    return youtube_playlist


async def convert_playlists_to_youtube_playlists(
    playlists: t.Iterable[Playlist],
) -> tuple[YouTubePlaylist, ...]:
    tasks: list[asyncio.Task[YouTubePlaylist]] = []

    for playlist in playlists:
        coro = convert_playlist_to_youtube_playlist(playlist)
        task = asyncio.create_task(coro)
        tasks.append(task)

    youtube_playlists: list[YouTubePlaylist] = await asyncio.gather(*tasks)
    return tuple(youtube_playlists)


def youtube_music_search_options(
    track: Track, youtube_music_search: YouTubeMusicSearch | None
) -> list[YouTubeMusicResult]:
    options: list[YouTubeMusicResult] = []

    if not youtube_music_search:
        return options

    if youtube_music_search.top_result:
        options.append(youtube_music_search.top_result)

    for youtube_music_song in youtube_music_search.songs:
        options.append(youtube_music_song)

    for youtube_music_video in youtube_music_search.videos:
        options.append(youtube_music_video)

    options.sort(key=lambda x: youtube_result_score(x, track), reverse=True)
    return options


async def convert_track_to_youtube_track(
    track: Track, client: httpx.AsyncClient, progress: Progress, task_id: TaskID
) -> YouTubeTrack | None:
    cached_tracks_dict: dict[
        Track, YouTubeTrack
    ] = await tracks_cache.load_cached_tracks_dict()
    cached_tracks: set[Track] = await tracks_cache.load_cached_tracks()

    advance = lambda: progress.advance(task_id, advance=1)

    if track in cached_tracks:
        advance()
        return cached_tracks_dict[track]

    youtube_music_search = await ytmusic.search_music(track.query, client=client)

    if not youtube_music_search:
        advance()
        rich.print(skipping_message(text=track.colorized_query, reason="No Results"))
        return None

    options = youtube_music_search_options(track, youtube_music_search)

    if not options:
        advance()
        rich.print(skipping_message(text=track.colorized_query, reason="No Results"))
        return None

    youtube_music_result = options[0]
    top_score = youtube_result_score(youtube_music_result, track)

    # value might need to be tweaked later
    if top_score < 1:
        advance()
        rich.print(
            skipping_message(
                text=track.colorized_query,
                reason=f"Low Score: [white]{round(top_score, 3)}[/white]",
            )
        )
        return None

    album_name: str | None = None
    is_explicit: bool | None = None

    if isinstance(youtube_music_result, YouTubeMusicSong):
        if youtube_music_result.album:
            album_name = youtube_music_result.album.name

        is_explicit = youtube_music_result.is_explicit

    youtube_track = YouTubeTrack(
        name=track.name,
        duration=track.duration,
        artists=track.artists,
        youtube_name=youtube_music_result.title,
        youtube_duration=youtube_music_result.duration,
        youtube_artists=tuple(
            Artist(name=x.name) for x in youtube_music_result.artists
        ),
        album_name=album_name,
        is_explicit=is_explicit,
        video_id=youtube_music_result.video_id,
    )

    advance()
    return youtube_track


async def fetch_youtube_tracks(
    tracks: t.Iterable[Track], progress: Progress, task_id: TaskID
) -> tuple[YouTubeTrack, ...]:
    async with httpx.AsyncClient(timeout=60) as client:
        youtube_tracks_tasks: list[asyncio.Task[YouTubeTrack | None]] = []

        for track in tracks:
            coro = convert_track_to_youtube_track(
                track=track, client=client, progress=progress, task_id=task_id
            )
            task = asyncio.create_task(coro)
            youtube_tracks_tasks.append(task)

        youtube_tracks: list[YouTubeTrack | None] = await asyncio.gather(*youtube_tracks_tasks)  # type: ignore
        youtube_tracks: tuple[YouTubeTrack, ...] = tuple(
            x for x in youtube_tracks if x is not None
        )

    return youtube_tracks


def remove_artist_from_title(title: str):
    dash_index = title.find(" - ")
    if dash_index == -1:
        return title

    return title[dash_index + 3 :]


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
    elif diff <= 10:
        return round(1 / diff, 2)
    else:
        return max(-1, -(round(diff / 10, 2) - 1))


def title_score(real_title: str, result_title: str) -> float:
    def remove_extraneous_data(title: str):
        return remove_artist_from_title(
            remove_features_from_title(remove_parens(title))
        ).strip()

    real_title = remove_extraneous_data(real_title.lower())
    result_title = remove_extraneous_data(result_title.lower())

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


def artists_score(
    real_artists: tuple[Artist, ...], result_artists: tuple[YouTubeMusicArtist, ...]
) -> float:
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
        return 0

    if real_album_name is None or result_album_name is None:
        return 0

    real_album_name = remove_parens(real_album_name.lower())
    result_album_name = remove_parens(result_album_name.lower())

    if real_album_name == result_album_name:
        return 1
    if real_album_name in result_album_name:
        return 0.75
    if result_album_name in real_album_name:
        return 0.75
    return 0
