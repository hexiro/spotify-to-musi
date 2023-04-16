"""Entrypoint and CLI handler."""
from __future__ import annotations

import asyncio
import functools
import typing as t

import oauth
import pyfy.excs
import rich
import rich_click as click
import spotify
from main import transfer_spotify_to_musi

from spotify_to_musi.paths import SPOTIFY_CREDENTIALS_PATH


def async_cmd(func: t.Callable) -> t.Callable:
    """
    Hack to make click support async commands.

    Reference:
        https://stackoverflow.com/q/67558717/10830115
    """

    @functools.wraps(func)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.group()
@async_cmd
async def cli() -> None:
    pass


@cli.command()
@async_cmd
@click.option(
    "-u",
    "--user",
    is_flag=True,
    help="Transfer liked songs and playlists of authorized user.",
    default=False,
    show_default=True,
)
@click.option(
    "-pl",
    "--playlist",
    help="Transfer Spotify playlist(s) by URL.",
    multiple=True,
    type=str,
)
async def transfer(user: bool, playlist: list[str]) -> None:
    """
    Transfer songs from Spotify to Musi.
    """

    await spotify.init()

    try:
        await spotify.spotify.me()
    except pyfy.excs.SpotifyError:
        rich.print(
            "[bold red]Spotify not authorized. Please run `[white]setup[/white]` first.[/bold red]"
        )
        return

    if not user and not playlist:
        rich.print(
            "[bold red]Failed to transfer. No playlist(s) nor the user's library were specified.[/bold red]"
        )
        return

    await transfer_spotify_to_musi(
        transfer_user_library=user, extra_playlist_urls=playlist
    )


@cli.command()
@async_cmd
async def setup() -> None:
    """
    Configure Spotify w/ OAuth.
    """
    spotify_to_musi_text = "[bold][green]Spotify[/green][reset]-to-[/reset][dark_orange3]Musi[/dark_orange3][/bold]"
    welcome_text = f"{spotify_to_musi_text} first time setup! [i grey53](Ctrl + C to exit)[/i grey53]"

    if SPOTIFY_CREDENTIALS_PATH.is_file():
        welcome_text += "\n[grey53]* Your secrets are already set! Only run this script if you need to authorize with Spotify again.[/grey53]"

    welcome_text += "\n"
    rich.print(welcome_text)

    rich.print(
        f"Your browser should now open. If not, navigate to [blue underline]{oauth.URL}[/blue underline].\nPlease authorize with Spotify and return once done.\n"
    )

    await oauth.run()

    try:
        await spotify.init()
        await spotify.spotify.me()
    except pyfy.excs.SpotifyError:  # spotipy.oauth2.SpotifyOauthError
        SPOTIFY_CREDENTIALS_PATH.unlink()
        rich.print(
            "[red]Uh Oh? Spotify isn't authorized. Please check your credentials.[/red]"
        )

    rich.print("[bold green]Spotify Authorized![/bold green]")


if __name__ == "__main__":
    cli()
