from __future__ import annotations

import contextlib
import json
import os
import re
import typing as t

import aiofiles

from spotify_to_musi.paths import SPOTIFY_CREDENTIALS_PATH

# https://regex101.com/r/r4mp7V/1
# works on tracks and playlists
SPOTIFY_ID_REGEX = re.compile(
    r"((https?:\/\/(.*?)(playlist|track)s?\/|spotify:(playlist|track):)(?P<id>.*))"
)


def task_description(*, querying: str, color: str, subtype: str | None = None) -> str:
    desc = f"[bold][{color}]Querying {querying}"

    if subtype is not None:
        desc += f" [ [white]{subtype}[/white] ] "

    desc += f"[/{color}][/bold]..."
    return desc


def loaded_message(
    *,
    source: str,
    loaded: str,
    color: str,
    name: str | None = None,
    tracks_count: int | None = None,
) -> str:
    msg = f"[bold {color}]{source.upper()}:[/bold {color}] Loaded {loaded} "

    tracks_parens = ("(", ")")
    if name is not None:
        tracks_parens = ("[", "]")
        msg += f"([grey53]{name}[/grey53]) "
    if tracks_count is not None:
        left, right = tracks_parens
        msg += f"{left}[{color}]{tracks_count}[/{color}] [grey53]tracks[/grey53]{right}"

    return msg


def skipping_message(*, text: str, reason: str) -> str:
    return (
        f"[bold yellow1]SKIPPING:[/bold yellow1] {text} [yellow1][{reason}][/yellow1]"
    )


async def load_spotify_credentials() -> dict[str, t.Any] | None:
    if not SPOTIFY_CREDENTIALS_PATH.is_file():
        return None

    async with aiofiles.open(SPOTIFY_CREDENTIALS_PATH, "r") as file:
        spotify_creds_text = await file.read()

    return json.loads(spotify_creds_text)


def spotify_client_credentials_from_file(
    spotify_creds_json: dict[str, t.Any]
) -> tuple[str, str] | None:
    def dict_or_env_value(
        data: dict[str, t.Any], key: str, env_variable: str | None = None
    ) -> str | None:
        """
        Gets a value from a provided dictionary or the system's environment variables.
        """
        with contextlib.suppress(KeyError):
            return data[key]
        with contextlib.suppress(KeyError):
            return os.environ[env_variable or key]
        return None

    client_id = dict_or_env_value(spotify_creds_json, "client_id", "SPOTIFY_CLIENT_ID")
    client_secret = dict_or_env_value(
        spotify_creds_json, "client_secret", "SPOTIFY_CLIENT_SECRET"
    )

    if not client_id or not client_secret:
        return None

    return client_id, client_secret


async def spotify_client_credentials() -> tuple[str, str] | None:
    # sourcery skip: assign-if-exp, reintroduce-else, swap-if-expression
    spotify_creds_json = await load_spotify_credentials()
    if not spotify_creds_json:
        return None
    return spotify_client_credentials_from_file(spotify_creds_json)


def remove_parens(title: str) -> str:
    bracket_groups = (
        ("[", "]"),
        ("(", ")"),
        ("{", "}"),
    )
    for left, right in bracket_groups:
        while left in title and right in title:
            left_index = title.index(left)
            right_index = title.index(right, left_index)

            title = title[:left_index] + title[right_index + 1 :]

    return title


def remove_features_from_title(title: str) -> str:
    ft_index = title.find("ft")
    feat_index = title.find("feat")

    featuring_index = ft_index if ft_index != -1 else feat_index

    if featuring_index != -1:
        title = title[:featuring_index]

    return title
