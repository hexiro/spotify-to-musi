import asyncio

import spotify
import musi
import youtube
import tracks_cache


async def main() -> None:
    spotify_playlists = await spotify.fetch_spotify_playlists()
    spotify_liked_tracks = await spotify.fetch_spotify_liked_tracks()

    playlists = await spotify.covert_spotify_playlists_to_playlists(spotify_playlists)
    liked_tracks = spotify.covert_spotify_tracks_to_tracks(spotify_liked_tracks)

    youtube_playlists = await youtube.convert_playlists_to_youtube_playlists(playlists)
    youtube_liked_tracks = await youtube.convert_tracks_to_youtube_tracks(liked_tracks)

    # musi_playlists = musi.convert_playlists_to_musi_playlists(youtube_playlists)
    # musi_library = musi.covert_youtube_tracks_to_musi_library(youtube_liked_tracks)

    # code = await musi.upload_to_musi(musi_library, musi_playlists)

    all_youtube_tracks = list(youtube_liked_tracks)
    for youtube_playlist in youtube_playlists:
        all_youtube_tracks.extend(youtube_playlist.tracks)

    await tracks_cache.cache_youtube_tracks(all_youtube_tracks)


if __name__ == "__main__":
    asyncio.run(main())
