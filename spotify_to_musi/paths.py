from __future__ import annotations

import pathlib
import sys

from spotify_to_musi.exceptions import UnsupportedPlatformError


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
    raise UnsupportedPlatformError(sys.platform)


APP_DATA = _app_data()

STM_PATH = APP_DATA / "spotify-to-musi"
STM_PATH.mkdir(exist_ok=True)
YOUTUBE_DATA_CACHE_PATH = STM_PATH / "youtube-data-cache.json"
SPOTIFY_CREDENTIALS_PATH = STM_PATH / "spotify-credentials.json"
