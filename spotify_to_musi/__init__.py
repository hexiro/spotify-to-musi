from pygments import highlight
import rich
from spotipy.oauth2 import SpotifyOAuth, SpotifyStateError

console = rich.get_console()

# monkey patch colors


def _get_auth_response_interactive(self: SpotifyOAuth, open_browser: bool = False):
    if open_browser:
        self._open_auth_url()
        prompt = "Enter the URL you were redirected to: "
    else:
        url = self.get_authorize_url()
        prompt = (
            f"[purple]Go to the following URL[/purple]: {url}\n"
            "[purple]Then, enter the URL you were redirected to[/purple]: "
        )
    response = console.input(prompt, markup=True)
    state, code = SpotifyOAuth.parse_auth_response_url(response)
    if self.state is not None and self.state != state:
        raise SpotifyStateError(self.state, state)
    return code


SpotifyOAuth._get_auth_response_interactive = _get_auth_response_interactive
