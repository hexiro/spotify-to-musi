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

if TYPE_CHECKING:
    from typehints.musi import MusiPlaylist, MusiVideo, MusiBackupResponse
    from typehints.spotify import SpotifyTrack, SpotifyPlaylistItem, CurrentUserPlaylists
    from typehints.youtube import YoutubeResult

# TODO: spotify liked songs --> musi library
# TODO: bulk search youtube videos

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(logging.Formatter(fmt="[%(levelname)s]: %(message)s"))
logger.addHandler(stream_handler)

dotenv.load_dotenv(".env")

SPOTIFY_CLIENT_ID: Final[str] = os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET: Final[str] = os.environ["SPOTIFY_CLIENT_SECRET"]
SPOTIFY_FIRST_TIME_SETUP = not os.path.exists("spotify.cache")

if SPOTIFY_FIRST_TIME_SETUP:
    logger.info("First time spotify setup, you will only have to do this once.")

spotify_oauth = spotipy.SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    scope="playlist-read-collaborative",
    redirect_uri="https://example.com/callback/",
    open_browser=False,
    cache_handler=spotipy.CacheFileHandler(cache_path="spotify.cache")
)
spotify = spotipy.Spotify(auth_manager=spotify_oauth)

def search_youtube(spotify_title: str) -> MusiVideo:
    def parse_duration(duration: str) -> int:
        minutes, seconds = duration.split(":")
        return (int(minutes) * 60) + int(seconds)

    query = youtubesearchpython.VideosSearch(spotify_title, limit=1)
    result: YoutubeResult = query.resultComponents[0]

    return {
        "created_date": time.time(),
        "video_duration": parse_duration(result["duration"]),
        "video_name": result["title"],
        "video_creator": result["channel"]["name"],
        "video_id": result["id"],
    }


if not SPOTIFY_FIRST_TIME_SETUP:
    logger.debug(f"{SPOTIFY_CLIENT_ID=}")
    logger.debug(f"{SPOTIFY_CLIENT_SECRET=}")
    logger.info("Fetching spotify playlists... ")

spotify_playlists: list[CurrentUserPlaylists] = spotify.current_user_playlists()["items"]
musi_playlists: dict[str, list[MusiVideo]] = defaultdict(list)

logger.info("Done!")
logger.debug(spotify_playlists)

for playlist in spotify_playlists:

    playlist_name = playlist["name"]
    playlist_id = playlist["id"]
    num_of_tracks = playlist["tracks"]["total"]

    logger.info(f"Starting to search playlist, {playlist_name}")
    logger.debug(f"num_of_tracks={num_of_tracks} id={playlist_id}")

    logger.info("Fetching tracks... ")
    tracks: list[SpotifyTrack] = []

    for offset in range(0, num_of_tracks, 100):
        items: list[SpotifyPlaylistItem] = spotify.playlist_items(playlist_id, offset=offset)["items"]
        for item in items:
            tracks.append(item["track"])

    logger.info("Done!")
    logger.debug(tracks)

    for track in tracks:
        song_artist = track["artists"][0]["name"]
        song_name = track["name"]
        spotify_title: str = f"{song_artist} - {song_name}"

        logger.info(f"Searching youtube for track, {spotify_title}")
        video = search_youtube(spotify_title)
        logger.info("Done!")
        logger.debug(video)

        if not video:
            continue
        musi_playlists[playlist_name].append(video)
    break

playlist_items: list[MusiVideo] = []
playlists: list[MusiPlaylist] = []
for name, videos in musi_playlists.items():
    playlist_items.extend(videos)
    playlists.append({
        "ot": "custom",
        "name": name,
        "type": "user",
        "date": int(time.time()),
        "items": [
            {"cd": int(vid["created_date"]), "pos": i, "video_id": vid["video_id"]} for i, vid in enumerate(videos)
        ]
    })

payload = {
    "library": {
        "ot": "custom",
        "items": [],
        "name": "My Library",
        "date": time.time(),
    },
    "playlist_items": playlist_items,
    "playlists": playlists,
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
