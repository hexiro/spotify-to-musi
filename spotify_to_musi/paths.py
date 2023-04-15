from __future__ import annotations

import pathlib
import sys


def _app_data() -> pathlib.Path:
    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming

    References:
        https://doc.qt.io/qt-5/qstandardpaths.html
    """
    home = pathlib.Path.home()
    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"
    raise RuntimeError("Unsupported platform")


APP_DATA = _app_data()

STM_PATH = APP_DATA / "spotify-to-musi"
STM_PATH.mkdir(exist_ok=True)
SPOTIFY_CACHE_PATH = STM_PATH / "spotify-cache.json"
SPOTIFY_DATA_PATH = STM_PATH / "spotify-data.json"
YOUTUBE_DATA_CACHE_PATH = STM_PATH / "youtube-data-cache.json"
SPOTIFY_CREDENTIALS_PATH = STM_PATH / "spotify-credentials.json"
