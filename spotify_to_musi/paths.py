from __future__ import annotations

import pathlib
import sys

__all__ = ("app_data", "spotify_cache_path")


def _app_data() -> pathlib.Path | None:
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
    return


app_data = _app_data()
assert app_data is not None

spotify_to_musi_path = app_data / "spotify-to-musi"
spotify_to_musi_path.mkdir(exist_ok=True)
spotify_cache_path = app_data / "spotify.cache.json"
spotify_data_path = app_data / "spotify.data.json"
data_cache_path = app_data / "data.cache.json"
