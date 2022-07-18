"""Entrypoint and CLI handler."""
from __future__ import annotations

import logging
import os

from typing import TYPE_CHECKING
import rich

import rich_click as click
import spotipy
import spotipy.oauth2
import spotipy.exceptions

from .commons import SPOTIFY_ID_REGEX
from .cache import has_unpatched_spotify_secrets, patch_spotify_secrets, store_spotify_secrets
from .main import get_spotify, transfer_spotify_to_musi
from .paths import spotify_cache_path, spotify_data_path


if TYPE_CHECKING:
    from .typings.spotify import SpotifyLikedSong, SpotifyPlaylist


click.rich_click.STYLE_OPTION = "bold magenta"
click.rich_click.STYLE_SWITCH = "bold blue"
click.rich_click.STYLE_METAVAR = "bold red"
click.rich_click.MAX_WIDTH = 75

console = rich.get_console()
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "-u",
    "--user",
    is_flag=True,
    help="Transfer liked songs and playlists of authorized user.",
    default=False,
    show_default=True,
)
@click.option("-pl", "--playlist", help="Transfer Spotify playlist(s) by URL.", multiple=True, type=str)
def transfer(user: bool, playlist: list[str]):
    """Transfer songs from Spotify to Musi."""
    if has_unpatched_spotify_secrets():
        patch_spotify_secrets()

    try:
        get_spotify()
    except spotipy.oauth2.SpotifyOauthError:
        console.print("[red]Spotify not authorized. Please run `setup` first.[/red]")
        return

    if not user and not playlist:
        console.print("[red]Not uploading user's playlists and no playlist(s) were specified.[/red]")
        return

    transfer_spotify_to_musi(user, playlist)


@cli.command()
def setup():
    """Configure Spotify API and other options."""
    grey = "#808080"
    spotify_to_musi_text = f"[bold][green]spotify[/green][reset]-to-[/reset][dark_orange3]musi[/dark_orange3][/bold]"
    welcome_text = f"Welcome to {spotify_to_musi_text} first time setup! [i](Ctrl + C to exit)[/i]"

    if has_unpatched_spotify_secrets():
        patch_spotify_secrets()
        welcome_text += (
            "\n* Your secrets are already set! Only run this script again if you need to authorize with Spotify again."
        )

    console.print(welcome_text, highlight=True, markup=True)

    def prompt(for_: str, default: str | None = None) -> str:
        default_text: str = ""
        if default:
            if len(default) > 5:
                mid_point = len(default) // 2
                default_fragment = f"{default[:mid_point]}..."
            else:
                default_fragment = default
            default_text = f" [{grey}][[i]{default_fragment}[/i]][/{grey}]"
        text = f"[magenta]{for_}{default_text}[/magenta]: "

        res = console.input(text) or default
        while not res:
            console.print("[red]Please enter a value.[/red]")
            res = console.input(text)
        return res

    spotify_client_id = prompt("Spotify Client ID", default=os.getenv("SPOTIPY_CLIENT_ID"))
    spotify_client_secret = prompt("Spotify Client Secret", default=os.getenv("SPOTIPY_CLIENT_SECRET"))
    store_spotify_secrets(spotify_client_id, spotify_client_secret)
    patch_spotify_secrets()
    try:
        get_spotify()
    except spotipy.oauth2.SpotifyOauthError:
        spotify_cache_path.unlink()
    try:
        get_spotify()
    except spotipy.oauth2.SpotifyOauthError:
        console.print("[red]Uh Oh? Spotify isn't authorized. Please check your credentials.[/red]")
        return
    console.print("[green]Spotify authorized![/green]")


if __name__ == "__main__":
    cli()
