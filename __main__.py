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

from typehints.general import SongAndVideo, DictSongAndVideo
from typehints.youtube import YoutubeResult

if TYPE_CHECKING:
    from typehints.musi import MusiPlaylist, MusiVideo, MusiBackupResponse, MusiItem
    from typehints.spotify import SpotifyTrack, SpotifyPlaylistItem, SpotifyPlaylist, SpotifyLikedSong

# TODO: cache song queries
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
songs: list[SongAndVideo] = []

# middle ground between spotify and musi
playlists: dict[str, list[SongAndVideo]] = defaultdict(list)
library: list[SongAndVideo] = []

# typed dicts for final request data
musi_items: list[MusiVideo] = []
musi_playlists: list[MusiPlaylist] = []
musi_library_items: list[MusiItem] = []

if os.path.exists("cache/data.cache.json"):
    with open("cache/data.cache.json") as file:
        cached_data: list[DictSongAndVideo] = json.load(file)
    logger.debug(f"{cached_data=}")
    for song in cached_data:
        deserialized = SongAndVideo(**song, is_from_cache=True)
        songs.append(deserialized)
    logger.debug(f"{songs=}")

if not SPOTIFY_FIRST_TIME_SETUP:
    logger.info("Done!")


def search(track: SpotifyTrack) -> SongAndVideo:
    """
    search cache and if not found search youtube.
    """
    artist_name = track["artists"][0]["name"]
    track_name = track["name"]

    cached_song = search_cache(artist_name, track_name)

    if cached_song:
        return cached_song
    else:
        return search_youtube(artist_name, track_name)


def search_cache(artist_name: str, track_name: str) -> SongAndVideo | None:
    logger.debug(f"Searching cache for artist, {artist_name!r} and name, {track_name!r}")
    search_cache = [song for song in songs if (song.spotify_artist == artist_name and
                                               song.spotify_name == track_name)]
    if not any(search_cache):
        return None

    cached_song = search_cache[0]
    logger.debug(f"found in cache!, {cached_song=}")
    return cached_song


def search_youtube(artist_name: str, track_name: str) -> SongAndVideo:
    def parse_duration(duration: str) -> int:
        minutes, seconds = duration.split(":")
        return (int(minutes) * 60) + int(seconds)

    search_query = f"{artist_name} - {track_name}"

    logger.info(f"Searching youtube for track, {search_query!r}")

    query = youtubesearchpython.VideosSearch(search_query, limit=1)
    result: YoutubeResult = query.resultComponents[0]

    logger.info("Done!")

    song = SongAndVideo(
        spotify_artist=artist_name,
        spotify_name=track_name,
        video_duration=parse_duration(result["duration"]),
        video_name=result["title"],
        video_creator=result["channel"]["name"],
        video_id=result["id"],
        is_from_cache=False
    )
    songs.append(song)
    return song


for liked_song in spotify_liked_songs:
    track = liked_song["track"]
    video = search(track)
    library.append(video)

for playlist in spotify_playlists:
    playlist_name = playlist["name"]
    playlist_id = playlist["id"]

    logger.info(f"Starting to search playlist, {playlist_name}")
    logger.info("Fetching tracks... ")

    # fetch tracks

    results = spotify.playlist_items(playlist_id)
    items: list[SpotifyPlaylistItem] = results["items"]
    while results["next"]:
        results = spotify.next(results)
        items.extend(results["items"])

    tracks: list[SpotifyTrack] = [item["track"] for item in items]
    logger.info("Done!")

    # handle tracks

    for track in tracks:
        video = search(track)
        playlists[playlist_name].append(video)

for name, videos in playlists.items():
    # add videos to global video catalog
    for vid in videos:
        musi_items.append(vid.to_musi_video())
    # add playlist
    musi_playlist_items = [vid.to_musi_item(index) for index, vid in enumerate(videos)]
    musi_playlist: MusiPlaylist = {
        "ot": "custom",
        "name": name,
        "type": "user",
        "date": int(time.time()),
        "items": musi_playlist_items
    }
    musi_playlists.append(musi_playlist)

# {"cd": int(vid["created_date"]), "pos": index, "video_id": vid["video_id"]}
for position, vid in enumerate(library):
    # add videos to global video catalog
    musi_items.append(vid.to_musi_video())
    # add library-specific videos
    musi_library_items.append(vid.to_musi_item(position))

# cache
cache: list[DictSongAndVideo] = [c.to_dict() for c in songs]

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
