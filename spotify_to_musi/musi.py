from typings.musi import MusiItem


def upload_to_musi() -> MusiBackupResponse:
    musi_items: list[MusiVideo] = []
    musi_playlists: list[MusiPlaylist] = []
    musi_library_items: list[MusiItem] = []

    payload = {
        "library": {"ot": "custom", "items": musi_library_items, "name": "My Library", "date": time.time()},
        "playlist_items": musi_items,
        "playlists": musi_playlists,
    }
