from __future__ import annotations
import logging
import sys

from typing import TYPE_CHECKING
from rich import print_json

import rich_click as click
import spotipy.exceptions

from spotify_to_musi.commons import SPOTIFY_ID_REGEX

from .cache import store_spotify_secrets
from .main import get_spotify, transfer_spotify_to_musi
from .paths import app_data, spotify_cache_path


if TYPE_CHECKING:
    from .typings.spotify import SpotifyLikedSong, SpotifyPlaylist


click.rich_click.STYLE_OPTION = "bold magenta"
click.rich_click.STYLE_SWITCH = "bold blue"
click.rich_click.STYLE_METAVAR = "bold red"
click.rich_click.MAX_WIDTH = 75

console = click.rich_click._get_rich_console()
logger = logging.getLogger(__name__)

logging.basicConfig(level="WARNING", stream=sys.stdout)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "-u/-nu",
    "--user/--no-user",
    is_flag=True,
    help="Transfer liked songs and playlists of authorized user.",
    default=True,
    show_default=True,
)
@click.option("-pl", "--playlist", help="Transfer Spotify playlist(s) by URL.", multiple=True, type=str)
def transfer(user: bool, playlist: list[str]):
    """Transfer songs from Spotify to Musi."""
    spotify = get_spotify()
    spotify_liked_songs: list[SpotifyLikedSong] = []
    spotify_playlists: list[SpotifyPlaylist] = []
    if user:
        spotify_liked_songs.extend(spotify.current_user_saved_tracks()["items"])
        spotify_playlists.extend(spotify.current_user_playlists()["items"])
    for playlist_link in playlist:
        match = SPOTIFY_ID_REGEX.match(playlist_link)
        playlist_id = match.group("id") if match else playlist_link
        try:
            pl = spotify.playlist(playlist_id)
        except spotipy.exceptions.SpotifyException:
            logger.warning(f"Unable to find playlist: {playlist_link}")
            continue
        spotify_playlists.append(pl)
        
    transfer_spotify_to_musi(spotify_liked_songs, spotify_playlists)


@cli.command()
def setup():
    """Configure Spotify API and other options."""
    welcome_text = "Welcome to [bold green]spotify-to-musi[/bold green] first time setup! [i](Ctrl + C to exit)[/i]"

    if spotify_cache_path and spotify_cache_path.is_file():
        welcome_text += "\n* You're already setup! Only run this script again if you're having issues."

    console.print(welcome_text, highlight=True, markup=True)

    def prompt(for_: str) -> str:
        # default_text = f" [#808080]\\[[i]{default}[/i]][/#808080]" if default else ""
        text = f"[magenta]{for_}[/magenta]: "

        res = console.input(text)
        while not res:
            console.print("[red]Please enter a value.[/red]")
            res = console.input(text)
        return res

    spotify_client_id = prompt("Spotify Client ID")
    spotify_client_secret = prompt("Spotify Client Secret")
    store_spotify_secrets(spotify_client_id, spotify_client_secret)
    get_spotify()


if __name__ == "__main__":
    cli()
