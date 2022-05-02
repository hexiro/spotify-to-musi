import re


# https://regex101.com/r/r4mp7V/1
# works on tracks and playlists
SPOTIFY_ID_REGEX = re.compile(r"((https?:\/\/(.*?)(playlist|track)s?\/|spotify:(playlist|track):)(?P<id>.*))")
