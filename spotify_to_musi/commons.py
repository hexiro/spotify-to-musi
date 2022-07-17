from __future__ import annotations
import hashlib
import json

import re
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from typing import Iterable
    from uuid import UUID
    from .typings.core import LikedSongs, Playlist


# https://regex101.com/r/r4mp7V/1
# works on tracks and playlists
SPOTIFY_ID_REGEX = re.compile(r"((https?:\/\/(.*?)(playlist|track)s?\/|spotify:(playlist|track):)(?P<id>.*))")


def compute_tracks_uuid(liked_songs: LikedSongs, playlists: list[Playlist]) -> UUID:
    # aims to use json.dumps to compute a hash of a tree of objects no matter the order
    # of the objects in the tree (if you have suggestions don't be afraid to shoot)

    def hash_json_tree(list_: Iterable[dict | list | list[dict]]) -> str:
        """
        Calculate md5 hash of list of dicts or list.
        """
        md5_hash = hashlib.md5()

        dumped_strings: list[str] = []

        for fragment in list_:
            if isinstance(fragment, list):
                dumped = hash_json_tree(fragment)
            else:
                dumped = json.dumps(fragment, sort_keys=True)
            dumped_strings.append(dumped)

        dumped_strings.sort()

        for dumped in dumped_strings:
            encoded = dumped.encode("utf-8")
            md5_hash.update(encoded)

        return md5_hash.hexdigest()

    # type is more specific than just a dict, so just round to simper types to make type checker happy
    liked_songs_dicts: list[dict] = [liked_song.to_dict() for liked_song in liked_songs]  # type: ignore
    playlists_dicts = [playlist.to_dict() for playlist in playlists]

    md5_liked_songs = hash_json_tree(liked_songs_dicts)
    md5_playlists = hash_json_tree(playlists_dicts)

    computed_uuid = uuid.uuid3(uuid.NAMESPACE_OID, md5_liked_songs + md5_playlists)
    return computed_uuid
