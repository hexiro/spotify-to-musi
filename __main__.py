from __future__ import annotations

import atexit
import json
import logging
import os
import pathlib
import queue
import threading
import time
import uuid
from collections import defaultdict
from json import JSONDecodeError
from typing import TYPE_CHECKING, Final

import dotenv
import requests
import rich
import spotipy
import youtubesearchpython
from requests_toolbelt import MultipartEncoder
from rich import traceback
from rich.logging import RichHandler
from rich.progress import Progress

from typehints.general import Track, Playlist

if TYPE_CHECKING:
    from typehints.general import TrackDict
    from typehints.youtube import YoutubeResult
    from typehints.musi import MusiPlaylist, MusiVideo, MusiItem, MusiBackupResponse
    from typehints.spotify import SpotifyTrack, SpotifyPlaylistItem, SpotifyPlaylist, SpotifyLikedSong

# TODO: bulk search youtube videos

dotenv.load_dotenv(".env")
console = rich.get_console()

traceback.install()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True, console=console)],
)
logger = logging.getLogger(__name__)

data_cache_path = pathlib.Path("./cache/data.cache.json")
spotify_cache_path = pathlib.Path("./cache/spotify.cache.json")

SPOTIFY_CLIENT_ID: Final[str] = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET: Final[str] = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_FIRST_TIME_SETUP: Final[bool] = not spotify_cache_path.is_file()

spotify_oauth = spotipy.SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    scope="user-library-read playlist-read-collaborative playlist-read-private",
    redirect_uri="https://example.com/callback/",
    open_browser=False,
    cache_handler=spotipy.CacheFileHandler(cache_path=str(spotify_cache_path)),
)
spotify = spotipy.Spotify(auth_manager=spotify_oauth)

if SPOTIFY_FIRST_TIME_SETUP:
    logger.info("First time spotify setup, you will only have to do this once.")
    if not spotify_cache_path.parent.is_dir():
        spotify_cache_path.parent.mkdir()

# spotify doesn't ensure credentials are valid before you call something,
# and it gets ugly if i make the first call inside the rich progress bar section.
# so i'm just gonna call a random func here
spotify.me()

# fetched from spotify
spotify_playlists: list[SpotifyPlaylist] = []
spotify_playlist_tracks: dict[str, list[SpotifyTrack]] = {}
spotify_liked_songs: list[SpotifyLikedSong] = []
spotify_liked_songs_tracks: list[SpotifyTrack] = []

# from cache, and global song catalog
tracks: list[Track] = []

# middle ground between spotify and musi
playlists: dict[Playlist, list[Track]] = defaultdict(list)
library: list[Track] = []

# typed dicts for final request data
musi_items: list[MusiVideo] = []
musi_playlists: list[MusiPlaylist] = []
musi_library_items: list[MusiItem] = []

if data_cache_path.is_file():
    try:
        with open(data_cache_path) as file:
            cached_data: list[TrackDict] = json.load(file)
        logger.debug(f"{cached_data=}")
        for track in cached_data:
            deserialized = Track(**track, is_from_cache=True)
            tracks.append(deserialized)
        logger.debug(f"{tracks=}")
    except JSONDecodeError:
        pass


def cache():
    logger.debug("caching!")
    cache_items: list[TrackDict] = [c.to_dict() for c in tracks]

    with open(data_cache_path, "w") as file:
        json.dump(cache_items, file, indent=4)


atexit.register(cache)


def search(spotify_track: SpotifyTrack, cache_only: bool = False) -> Track:
    """
    search cache and if not found search youtube.
    """
    artist = spotify_track["artists"][0]["name"]
    song = spotify_track["name"]

    cached_track = search_cache(artist, song)

    if cached_track or cache_only:
        return cached_track
    else:
        return search_youtube(artist, song)


def search_cache(artist: str, song: str) -> Track | None:
    logger.debug(f"Searching cache for artist, {artist!r} and name, {song!r}")
    search_cache = [e for e in tracks if (e.artist == artist and e.song == song)]
    if not any(search_cache):
        return None

    cached_song = search_cache[0]
    logger.debug(f"found in cache!, {cached_song=}")
    return cached_song


def search_youtube(artist: str, song: str) -> Track:
    def parse_duration(duration: str) -> int:
        minutes, seconds = duration.split(":")
        return (int(minutes) * 60) + int(seconds)

    search_query = f"{artist} - {song} (Official Audio)"

    logger.info(f"Searching youtube for track, {search_query!r}")

    query = youtubesearchpython.VideosSearch(search_query, limit=1)
    result: YoutubeResult = query.resultComponents[0]

    title: str = result["title"]
    channel_name: str = result["channel"]["name"]

    logger.info(f"Done! {title=!r} {channel_name=!r}")

    track = Track(
        artist=artist,
        song=song,
        duration=parse_duration(result["duration"]),
        video_id=result["id"],
    )
    tracks.append(track)
    return track


# querying spotify...
with Progress(console=console, transient=True) as progress:
    task_query_spotify = progress.add_task("[green]Querying Spotify...", total=2)

    spotify_liked_songs = spotify.current_user_saved_tracks()["items"]

    for liked_song in spotify_liked_songs:
        spotify_track = liked_song["track"]
        spotify_liked_songs_tracks.append(spotify_track)

    progress.advance(task_query_spotify)
    spotify_playlists = spotify.current_user_playlists()["items"]

    for spotify_playlist in spotify_playlists:
        playlist_id = spotify_playlist["id"]
        playlist_name = spotify_playlist["name"]

        results = spotify.playlist_items(playlist_id)
        items: list[SpotifyPlaylistItem] = results["items"]
        while results["next"]:
            results = spotify.next(results)
            items.extend(results["items"])

        spotify_playlist_tracks[playlist_name] = [item["track"] for item in items]

    progress.advance(task_query_spotify)

# searching youtube...
with Progress(console=console, transient=True) as progress:
    task_searching_youtube = progress.add_task("[red]Searching YouTube...", start=False, advance=1)
    spotify_tracks_to_search = queue.Queue(maxsize=0)

    for spotify_track in spotify_liked_songs_tracks:
        spotify_tracks_to_search.put(spotify_track)

    for spotify_tracks in spotify_playlist_tracks.values():
        for spotify_track in spotify_tracks:
            spotify_tracks_to_search.put(spotify_track)

    progress.update(task_searching_youtube, total=spotify_tracks_to_search.qsize())
    progress.start_task(task_searching_youtube)


    def search_and_advance():
        thread = threading.current_thread()
        while spotify_tracks_to_search.qsize() > 0:
            if not thread.is_alive():
                return
            spotify_track = spotify_tracks_to_search.get()
            search(spotify_track)
            progress.advance(task_searching_youtube)
            spotify_tracks_to_search.task_done()


    # python threading w/o blocking KeyboardInterrupt
    # reference: http://gregoryzynda.com/python/developer/threading/2018/12/21/interrupting-python-threads.html

    threads: list[threading.Thread] = []
    for i in range(5):
        try:
            thread = threading.Thread(target=search_and_advance, daemon=True)
            threads.append(thread)
            thread.start()
        except KeyboardInterrupt as e:
            thread.join()
            raise e

    for thread in threads:
        while thread.is_alive():
            thread.join(0.5)

# sending to musi...
with Progress(console=console, transient=True) as progress:
    task_sending_to_musi = progress.add_task("[orange]Sending to Musi...", advance=1, total=4)

    for spotify_playlist in spotify_playlists:
        playlist_name = spotify_playlist["name"]
        playlist_id = spotify_playlist["id"]
        playlist_cover_url = spotify_playlist["images"][0]["url"]
        # handle tracks

        # immutable. If a playlist with the exact same params are made it will map to the same item in the dict.
        playlist = Playlist(playlist_name, playlist_cover_url)
        spotify_tracks = spotify_playlist_tracks[playlist_name]

        for spotify_track in spotify_tracks:
            track = search(spotify_track, cache_only=True)
            playlists[playlist].append(track)

    progress.advance(task_sending_to_musi)

    for playlist, playlist_tracks in playlists.items():
        # add tracks to global video catalog
        for track in playlist_tracks:
            musi_items.append(track.to_musi_video())
        # add playlist
        musi_playlist_items = [track.to_musi_item(position) for position, track in enumerate(playlist_tracks)]
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

    for position, track in enumerate(library):
        # add track to global video catalog
        musi_items.append(track.to_musi_video())
        # add library-specific videos
        musi_library_items.append(track.to_musi_item(position))

    progress.advance(task_sending_to_musi)

    logger.debug(f"{musi_library_items=}")
    logger.debug(f"{musi_items=}")
    logger.debug(f"{musi_playlists=}")

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
    resp = requests.post("https://feelthemusi.com/api/v4/backups/create", data=multipart_encoder, headers=headers)
    backup: MusiBackupResponse = resp.json()

    progress.advance(task_sending_to_musi)

    logger.info(f"{backup['success']} code={backup['code']}")

console.print(f"[red]Success! use code, [bold]{backup['code']}[/bold] on Musi to restore your songs from Spotify.")
