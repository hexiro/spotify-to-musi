import asyncio

import rich

import spotify
import musi
import youtube
import tracks_cache

from rich.progress import Progress


async def main() -> None:
    spotify_to_musi_rich_text = (
        f"[bold][green4]SPOTIFY-[/green4][grey53]TO[/grey53]-[dark_orange3]MUSI[/dark_orange3][/bold]"
    )

    with Progress() as progress:
        spotify_playlists, spotify_liked_tracks = await spotify.query_spotify(progress)

        return

        # TODO: de-deduplicate tracks when requesting ytm

        playlists = spotify.covert_spotify_playlists_to_playlists(spotify_playlists)
        rich.print(f"{spotify_to_musi_rich_text} fetched {len(spotify_playlists)} playlists")
        liked_tracks = spotify.covert_spotify_tracks_to_tracks(spotify_liked_tracks)
        rich.print(f"{spotify_to_musi_rich_text} fetched {len(liked_tracks)} liked tracks")

        await tracks_cache.load_cached_youtube_tracks()

        youtube_playlists = await youtube.convert_playlists_to_youtube_playlists(playlists)
        rich.print(f"{spotify_to_musi_rich_text} fetched {len(spotify_playlists)} youtube playlists")
        youtube_liked_tracks = await youtube.convert_tracks_to_youtube_tracks(liked_tracks)
        rich.print(f"{spotify_to_musi_rich_text} fetched {len(youtube_liked_tracks)} youtube liked tracks")

        all_youtube_tracks = list(youtube_liked_tracks)
        for youtube_playlist in youtube_playlists:
            all_youtube_tracks.extend(youtube_playlist.tracks)

        await tracks_cache.cache_youtube_tracks(all_youtube_tracks)

        musi_playlists = musi.convert_playlists_to_musi_playlists(youtube_playlists)
        musi_library = musi.covert_youtube_tracks_to_musi_library(youtube_liked_tracks)

        backup = await musi.upload_to_musi(musi_playlists, musi_library)

    rich.print(f"[bold][dark_orange3]MUSI CODE[/dark_orange3]: [white]{backup.code}[/white][/bold]")


if __name__ == "__main__":
    asyncio.run(main())
