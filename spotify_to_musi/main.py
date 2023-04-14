import asyncio

import rich

import spotify
import musi
import youtube
import tracks_cache

from rich.progress import Progress


async def main() -> None:
    with Progress() as progress:
        playlists, liked_tracks = await spotify.query_spotify(progress)

        # TODO: de-deduplicate tracks when requesting ytm

        await tracks_cache.load_cached_youtube_tracks()

        youtube_playlists, youtube_liked_tracks = await youtube.query_youtube(progress, playlists, liked_tracks)

        await tracks_cache.cache_youtube_tracks(youtube_playlists, youtube_liked_tracks)

        musi_playlists, musi_library = musi.convert_from_youtube(youtube_playlists, youtube_liked_tracks)
        backup = await musi.upload_to_musi(musi_playlists, musi_library)

    rich.print(f"[bold][dark_orange3]MUSI CODE[/dark_orange3]: [white]{backup.code}[/white][/bold]")


if __name__ == "__main__":
    asyncio.run(main())
