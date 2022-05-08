from __future__ import annotations

import functools
import json
import logging
import math
import queue
import threading
import datetime
import time
from typing import TYPE_CHECKING
import uuid

import requests
import rich
import rich_click as click
import youtubesearchpython
import spotipy
from rich.progress import Progress
from requests_toolbelt import MultipartEncoder

from .typings.core import Playlist, Track, TrackData
from .cache import cache_tracks, get_cached_tracks, patch_spotify_secrets
from .paths import spotify_cache_path

if TYPE_CHECKING:
    from .typings.core import LikedSongs
    from .typings.musi import MusiItem, MusiPlaylist, MusiVideo, MusiBackupResponse
    from .typings.youtube import YoutubeResult
    from .typings.spotify import SpotifyPlaylistItem
    from .typings.spotify import SpotifyLikedSong, SpotifyPlaylist, SpotifyTrack

console = rich.get_console()
logger = logging.getLogger(__name__)
cached_tracks: list[Track] = get_cached_tracks()


@functools.lru_cache()
def get_spotify() -> spotipy.Spotify:
    """Returns spotify instance"""
    cache_handler = spotipy.CacheFileHandler(cache_path=str(spotify_cache_path))
    spotify_oauth = spotipy.SpotifyOAuth(
        scope="user-library-read playlist-read-collaborative playlist-read-private",
        redirect_uri="https://example.com/callback/",
        open_browser=False,
        cache_handler=cache_handler,
    )
    spotify = spotipy.Spotify(auth_manager=spotify_oauth)
    spotify.me()
    return spotify


def spotify_track_to_track(spotify_track: SpotifyTrack) -> Track | None:
    if spotify_track["is_local"]:
        return None
    try:
        artist = spotify_track["artists"][0]["name"]
        song = spotify_track["name"]
    except (KeyError, TypeError):
        return None
    return Track(artist, song)


def get_spotify_playlist_tracks(spotify_playlists: list[SpotifyPlaylist]) -> list[Playlist]:
    spotify = get_spotify()
    playlists: list[Playlist] = []

    for spotify_playlist in spotify_playlists:
        playlist_name = spotify_playlist["name"]
        playlist_id = spotify_playlist["id"]
        playlist_cover_url = spotify_playlist["images"][0]["url"]

        pl = Playlist(playlist_name, playlist_id, playlist_cover_url)

        results = spotify.playlist_items(playlist_id)
        items: list[SpotifyPlaylistItem] = results["items"]

        while results["next"]:  # type: ignore
            results = spotify.next(results)
            items.extend(results["items"])  # type: ignore

        for item in items:
            spotify_track = item["track"]
            track = spotify_track_to_track(spotify_track)
            if not track:
                continue
            pl.tracks.append(track)
        playlists.append(pl)

    return playlists


def get_spotify_liked_songs_tracks(spotify_liked_songs: list[SpotifyLikedSong]) -> LikedSongs:
    tracks: list[Track] = []
    for liked_song in spotify_liked_songs:
        spotify_track = liked_song["track"]
        spotify_track.pop("available_markets", None)  # type: ignore
        track = spotify_track_to_track(spotify_track)
        if not track:
            continue
        tracks.append(track)
    return tracks


def search_cache_for_track(track: Track) -> TrackData | None:
    logger.debug(f"Searching cache for artist, {track.artist!r} and name, {track.song!r}")
    try:
        index = cached_tracks.index(track)
        cached_track = cached_tracks[index]
    except ValueError:
        return None
    logger.debug(f"found in cache!, {cached_track=}")

    duration = cached_track.duration
    video_id = cached_track.video_id
    if not video_id or duration == -1:
        return None
    return TrackData(duration, video_id)


def search_youtube_for_track(track: Track) -> TrackData | None:
    def parse_duration(duration: str) -> int:
        map = {
            0: "seconds",
            1: "minutes",
            2: "hours",
        }
        time_map = {}
        for index, metric in enumerate(reversed(duration.split(":"))):
            unit = map[index]
            time_map[unit] = int(metric)
        t = datetime.timedelta(**time_map)
        seconds = math.ceil(t.total_seconds())
        return seconds

    search_query = f"{track.artist} - Topic - {track.song} (Official Audio)"
    logger.debug(f"Searching youtube for track, {search_query!r}")

    search = youtubesearchpython.VideosSearch(search_query, limit=1)
    try:
        result: YoutubeResult = search.result()["result"][0]  # type: ignore
    except IndexError:
        logger.warning(f"can't find YouTube video for song: \"{track.artist} - {track.song}\"")
        return None

    logger.debug(f"{result=}")

    title: str = result["title"]
    channel_name: str = result["channel"]["name"]

    logger.debug(f"Done! {title=!r} {channel_name=!r}")

    duration = parse_duration(result["duration"])
    video_id = result["id"]
    return TrackData(duration, video_id)


def load_track_data(track: Track) -> None:
    """
    search cache and if not found search youtube.
    """
    artist = track.artist
    song = track.song

    logger.info(f"searching for track: {track!r}")

    track_data: TrackData | None = search_cache_for_track(track)

    if not track_data:
        track_data = search_youtube_for_track(track)

    if not track_data:
        return

    logger.info(f"done! {track=!r} video_id={track.video_id} artist={artist} song={song}")

    track.duration = track_data.duration
    track.video_id = track_data.video_id
    assert track.loaded


def query_spotify(
    liked_songs: list[SpotifyLikedSong], spotify_playlists: list[SpotifyPlaylist]
) -> tuple[LikedSongs, list[Playlist]]:
    with Progress(console=console, transient=True) as progress:
        task_query_spotify = progress.add_task("[green]Querying Spotify...", total=2)
        spotify_liked_songs_tracks = get_spotify_liked_songs_tracks(liked_songs)
        progress.advance(task_query_spotify)
        spotify_playlist_tracks = get_spotify_playlist_tracks(spotify_playlists)
        progress.advance(task_query_spotify)
    return spotify_liked_songs_tracks, spotify_playlist_tracks


def search_youtube(liked_songs: LikedSongs, playlists: list[Playlist]) -> None:
    with Progress(console=console, transient=True) as progress:
        task_searching_youtube = progress.add_task("[red]Searching YouTube...", start=False, advance=1)
        tracks_to_search: queue.Queue[Track] = queue.Queue(maxsize=0)
        all_tracks: list[Track] = []

        for playlist in playlists:
            for track in playlist.tracks:
                tracks_to_search.put(track)
                all_tracks.append(track)

        for track in liked_songs:
            tracks_to_search.put(track)
            all_tracks.append(track)

        progress.update(task_searching_youtube, total=tracks_to_search.qsize())
        progress.start_task(task_searching_youtube)

        def search_and_advance():
            thread = threading.current_thread()
            while tracks_to_search.qsize() > 0:
                if not thread.is_alive():
                    return
                track = tracks_to_search.get()
                if not track:
                    continue
                load_track_data(track)
                # adding to list from multiple threads --
                # not sure if this has side-effects
                if track:
                    cached_tracks.append(track)
                progress.advance(task_searching_youtube)
                tracks_to_search.task_done()

        # python threading w/o blocking KeyboardInterrupt
        # reference: http://gregoryzynda.com/python/developer/threading/2018/12/21/interrupting-python-threads.html

        threads: list[threading.Thread] = []
        for _ in range(5):
            thread = threading.Thread(target=search_and_advance, daemon=True)
            threads.append(thread)
            try:
                thread.start()
            except KeyboardInterrupt as e:
                thread.join()
                raise e

        for thread in threads:
            while thread.is_alive():
                thread.join(0.5)


def upload_to_musi(liked_songs: LikedSongs, playlists: list[Playlist]) -> str | None:
    with Progress(console=console, transient=True) as progress:
        musi_items: list[MusiVideo] = []
        musi_playlists: list[MusiPlaylist] = []
        musi_library_items: list[MusiItem] = []

        task_sending_to_musi = progress.add_task("[orange]Sending to Musi...", advance=1, total=3)

        for playlist in playlists:
            # playlist_name = spotify_playlist["name"]
            # playlist_cover_url = spotify_playlist["images"][0]["url"]
            # handle tracks

            # immutable. If a playlist with the exact same params are made it will map to the same item in the dict.
            # playlist = Playlist(playlist_name, playlist_cover_url)
            # logger.debug(f"{playlist=}")
            # spotify_tracks = spotify_playlist_tracks[playlist_name]

            tracks = [track for track in playlist.tracks if track.loaded]
            # add tracks to global video catalog
            for track in tracks:
                musi_video = track.to_musi_video()
                musi_items.append(musi_video)
            # add playlist
            musi_playlist_items = [track.to_musi_item(position) for position, track in enumerate(tracks)]
            musi_playlist: MusiPlaylist = {
                "ot": "custom",
                "name": playlist.name,
                "type": "user",
                "date": int(time.time()),
                "items": musi_playlist_items,
                "ciu": playlist.cover_url,
            }
            musi_playlists.append(musi_playlist)

        progress.advance(task_sending_to_musi)

        for position, track in enumerate(liked_songs):
            # add track to global video catalog
            musi_items.append(track.to_musi_video())
            # add library-specific videos
            musi_library_items.append(track.to_musi_item(position))

        progress.advance(task_sending_to_musi)

        payload = {
            "library": {"ot": "custom", "items": musi_library_items, "name": "My Library", "date": time.time()},
            "playlist_items": musi_items,
            "playlists": musi_playlists,
        }
        multipart_encoder = MultipartEncoder(
            fields={"data": json.dumps(payload), "uuid": str(uuid.uuid4())},
            boundary=f"Boundary+Musi{uuid.uuid4()}",
        )
        headers = {
            "Content-Type": multipart_encoder.content_type,
            "User-Agent": "Musi/25691 CFNetwork/1206 Darwin/20.1.0",
        }
        resp = requests.post(
            "https://feelthemusi.com/api/v4/backups/create", data=multipart_encoder, headers=headers  # type: ignore
        )

        backup: MusiBackupResponse = resp.json()
        progress.advance(task_sending_to_musi)
        logger.info(f"{backup['success']} code={backup['code']}")
        code = backup.get("code")

    return code


def transfer_spotify_to_musi(
    spotify_liked_songs: list[SpotifyLikedSong], spotify_playlists: list[SpotifyPlaylist]
) -> None:

    # TODO: handle error handling in yt search better.

    liked_songs, playlists = query_spotify(spotify_liked_songs, spotify_playlists)
    search_youtube(liked_songs, playlists)

    all_tracks = set(cached_tracks)
    for liked_song in liked_songs:
        all_tracks.add(liked_song)
    for pl in playlists:
        for track in pl.tracks:
            all_tracks.add(track)

    cache_tracks(all_tracks)

    if not liked_songs and not playlists:
        console.print("[red]No tracks to upload.[/red]")
        return

    code = upload_to_musi(liked_songs, playlists)
    console.print(f"[green]Success! use code, [bold]{code}[/bold] on Musi to restore your songs from Spotify.[/green]")
