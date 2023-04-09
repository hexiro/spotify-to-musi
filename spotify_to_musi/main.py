import asyncio

import rich

import spotify
import youtube


async def main() -> None:
    # spotify_playlists = await spotify.fetch_spotify_playlists()
    spotify_liked_tracks = await spotify.fetch_spotify_liked_tracks()

    # playlists = await spotify.covert_spotify_playlists_to_playlists(spotify_playlists)
    liked_tracks = spotify.covert_spotify_tracks_to_tracks(spotify_liked_tracks)

    youtube_liked_tracks = await youtube.convert_tracks_to_youtube_tracks(liked_tracks[:10])

    rich.print(youtube_liked_tracks)


if __name__ == "__main__":
    asyncio.run(main())
