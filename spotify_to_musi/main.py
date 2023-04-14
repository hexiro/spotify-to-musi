import asyncio

import rich

import spotify
import musi
import youtube

from rich.progress import Progress


async def main() -> None:
    with Progress() as progress:
        playlists, liked_tracks = await spotify.query_spotify(progress)
        youtube_playlists, youtube_liked_tracks = await youtube.query_youtube(playlists, liked_tracks, progress)
        musi_playlists, musi_library = musi.convert_from_youtube(youtube_playlists, youtube_liked_tracks)

        backup = await musi.upload_to_musi(musi_playlists, musi_library)

    rich.print(f"[bold][dark_orange3]MUSI CODE[/dark_orange3]: [white]{backup.code}[/white][/bold]")


if __name__ == "__main__":
    asyncio.run(main())
