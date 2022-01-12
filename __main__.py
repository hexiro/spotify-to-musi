from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING, Final

import dotenv
import requests
import spotipy
import youtubesearchpython
from requests_toolbelt import MultipartEncoder

from typehints.general import Track

if TYPE_CHECKING:
    from typehints.general import TrackDict
    from typehints.youtube import YoutubeResult
    from typehints.musi import MusiPlaylist, MusiVideo, MusiBackupResponse, MusiItem
    from typehints.spotify import SpotifyTrack, SpotifyPlaylistItem, SpotifyPlaylist, SpotifyLikedSong

# TODO: bulk search youtube videos

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(logging.Formatter(fmt="[%(levelname)s]: %(message)s"))
logger.addHandler(stream_handler)

dotenv.load_dotenv(".env")

SPOTIFY_CLIENT_ID: Final[str] = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET: Final[str] = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_FIRST_TIME_SETUP = not os.path.isdir("cache")

if SPOTIFY_FIRST_TIME_SETUP:
    os.mkdir("cache")
    logger.info("First time spotify setup, you will only have to do this once.")

spotify_oauth = spotipy.SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    scope="user-library-read playlist-read-collaborative",
    redirect_uri="https://example.com/callback/",
    open_browser=False,
    cache_handler=spotipy.CacheFileHandler(cache_path="cache/spotify.cache.json"),
)
spotify = spotipy.Spotify(auth_manager=spotify_oauth)

if not SPOTIFY_FIRST_TIME_SETUP:
    logger.debug(f"{SPOTIFY_CLIENT_ID=}")
    logger.debug(f"{SPOTIFY_CLIENT_SECRET=}")
    logger.info("Fetching spotify playlists... ")
    logger.info("Fetching spotify liked songs... ")

# fetched from spotify
spotify_playlists: list[SpotifyPlaylist] = spotify.current_user_playlists()["items"]
spotify_liked_songs: list[SpotifyLikedSong] = spotify.current_user_saved_tracks()["items"]

# from cache, and global song catalog
tracks: list[Track] = []

# middle ground between spotify and musi
playlists: dict[str, list[Track]] = defaultdict(list)
library: list[Track] = []

# typed dicts for final request data
musi_items: list[MusiVideo] = []
musi_playlists: list[MusiPlaylist] = []
musi_library_items: list[MusiItem] = []

if os.path.exists("cache/data.cache.json"):
    with open("cache/data.cache.json") as file:
        cached_data: list[TrackDict] = json.load(file)
    logger.debug(f"{cached_data=}")
    for track in cached_data:
        deserialized = Track(**track, is_from_cache=True)
        tracks.append(deserialized)
    logger.debug(f"{tracks=}")

if not SPOTIFY_FIRST_TIME_SETUP:
    logger.info("Done!")


def search(spotify_track: SpotifyTrack) -> Track:
    """
    search cache and if not found search youtube.
    """
    artist = spotify_track["artists"][0]["name"]
    song = spotify_track["name"]

    cached_track = search_cache(artist, song)

    if cached_track:
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


for liked_song in spotify_liked_songs:
    spotify_track = liked_song["track"]
    track = search(spotify_track)
    library.append(track)

for spotify_playlist in spotify_playlists:
    playlist_name = spotify_playlist["name"]
    playlist_id = spotify_playlist["id"]

    logger.info(f"Starting to search playlist, {playlist_name}")
    logger.info("Fetching tracks... ")

    # fetch tracks

    results = spotify.playlist_items(playlist_id)
    items: list[SpotifyPlaylistItem] = results["items"]
    while results["next"]:
        results = spotify.next(results)
        items.extend(results["items"])

    spotify_tracks: list[SpotifyTrack] = [item["track"] for item in items]
    logger.info("Done!")

    # handle tracks

    for spotify_track in spotify_tracks:
        video = search(spotify_track)
        playlists[playlist_name].append(video)

for name, playlist_tracks in playlists.items():
    # add tracks to global video catalog
    for track in playlist_tracks:
        musi_items.append(track.to_musi_video())
    # add playlist
    musi_playlist_items = [track.to_musi_item(index) for index, track in enumerate(playlist_tracks)]
    musi_playlist: MusiPlaylist = {
        "ot": "custom",
        "name": name,
        "type": "user",
        "date": int(time.time()),
        "items": musi_playlist_items
    }
    musi_playlists.append(musi_playlist)

# {"cd": int(vid["created_date"]), "pos": index, "video_id": vid["video_id"]}
for position, track in enumerate(library):
    # add track to global video catalog
    musi_items.append(track.to_musi_video())
    # add library-specific videos
    musi_library_items.append(track.to_musi_item(position))

# cache
cache: list[TrackDict] = [c.to_dict() for c in tracks]

with open("cache/data.cache.json", "w") as file:
    json.dump(cache, file, indent=4)

logger.debug(f"{musi_library_items=}")
logger.debug(f"{musi_items=}")
logger.debug(f"{musi_playlists=}")

payload = {
    "library": {
        "ot": "custom",
        "items": musi_library_items,
        "name": "My Library",
        "date": time.time()
    },
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
logger.info(f"{backup['success']} code={backup['code']}")
