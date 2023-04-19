from __future__ import annotations

import asyncio

import musi
import rich
import spotify
import youtube
from rich.progress import Progress


async def transfer_spotify_to_musi(*, transfer_user_library: bool, extra_playlist_urls: list[str]) -> None:
    with Progress() as progress:
        playlists, liked_tracks = await spotify.query_spotify(transfer_user_library, extra_playlist_urls, progress)
        youtube_playlists, youtube_liked_tracks = await youtube.query_youtube(playlists, liked_tracks, progress)
        musi_playlists, musi_library = musi.convert_from_youtube(youtube_playlists, youtube_liked_tracks)

        backup = await musi.upload_to_musi(musi_playlists, musi_library)

    import_style = "OVERWRITE" if transfer_user_library else "MERGE"
    rich.print(f"[bold][dark_orange3]MUSI CODE:[/dark_orange3] [white]{backup.code}[/white][/bold]")
    rich.print(f"[bold][dark_orange3]MUSI IMPORT:[/dark_orange3]: [white]{import_style}[/white][/bold]")
