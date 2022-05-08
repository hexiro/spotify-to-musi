from __future__ import annotations

import logging

import rich
import rich.logging
from spotipy.oauth2 import SpotifyOAuth, SpotifyStateError


logger = logging.getLogger(__name__)
rich_handler = rich.logging.RichHandler(show_time=False, rich_tracebacks=True, show_path=False)
logging.basicConfig(level="WARNING", format="%(message)s", force=True, handlers=[rich_handler])


console = rich.get_console()

# monkey patch colors


def _get_auth_response_interactive(self: SpotifyOAuth, open_browser: bool = False):
    url = self.get_authorize_url()
    prompt = (
        f"[magenta]Go to the following URL[/magenta]: {url}\n"
        "[magenta]Then, enter the URL you were redirected to[/magenta]: "
    )
    response = console.input(prompt, markup=True)
    state, code = SpotifyOAuth.parse_auth_response_url(response)
    if self.state is not None and self.state != state:
        raise SpotifyStateError(self.state, state)
    return code


SpotifyOAuth._get_auth_response_interactive = _get_auth_response_interactive
