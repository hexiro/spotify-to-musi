"""Entrypoint and CLI handler."""
from __future__ import annotations

import asyncio
import contextlib
import functools
import os
import typing as t

import main
import oauth
import pyfy.excs
import rich
import rich_click as click
import spotify
from rich.prompt import Prompt

from spotify_to_musi.commons import (load_spotify_credentials,
                                     spotify_client_credentials,
                                     spotify_client_credentials_from_file)
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

    await main.transfer_spotify_to_musi(
        transfer_user_library=user, extra_playlist_urls=playlist
    )


@cli.command()
@async_cmd
async def setup() -> None:
    """
    Configure Spotify w/ OAuth.
    """
    spotify_to_musi_text = "[bold][green]Spotify[/green][reset]-to-[/reset][dark_orange3]Musi[/dark_orange3][/bold]"
    welcome_text = f"{spotify_to_musi_text} first time setup! [i grey53](Ctrl + C to exit)[/i grey53]\n"

    client_id: str | None = None
    client_secret: str | None = None

    spotify_client_creds = await spotify_client_credentials()
    if spotify_client_creds:
        client_id, client_secret = spotify_client_creds

    if client_id and client_secret:
        welcome_text += "[grey53]* Your secrets are already set! Only run this script if you need to authorize with Spotify again.[/grey53]\n"

    rich.print(welcome_text)

    def style_prompt(prompt: str) -> str:
        return f"[bold white]{prompt}[/bold white][grey53]"

    spotify_client_id: str = Prompt.ask(
        style_prompt("Spotify Client ID"), default=client_id
    )  # type: ignore
    spotify_client_secret: str = Prompt.ask(
        style_prompt("Spotify Client Secret"), default=client_secret
    )  # type: ignore

    rich.print(
        f"\nPlease open your browser and navigate to [blue underline]{oauth.URL}[/blue underline].\nAuthorize with Spotify and return once done.\n"
    )

    await oauth.run(
        spotify_client_id=spotify_client_id,
        spotify_client_secret=spotify_client_secret,
    )

    try:
        await spotify.init()
        await spotify.spotify.me()
    except pyfy.excs.SpotifyError:
        SPOTIFY_CREDENTIALS_PATH.unlink()
        rich.print(
            "[red]Uh Oh? Spotify isn't authorized. Please check your credentials.[/red]"
        )

    rich.print("[bold green]Spotify Authorized![/bold green]")


if __name__ == "__main__":
    cli()
