### constants

# from ytmusicapi

import asyncio
import contextlib
import itertools
import time
import httpx
import typing as t
import rich
import json

from datatypes import YouTubeMusicVideo
from datatypes import YouTubeMusicSong
from datatypes import TopResult
from datatypes import YoutubeMusicSearch


YT_MUSIC_DOMAIN = "https://music.youtube.com"
YT_MUSIC_BASE_API = YT_MUSIC_DOMAIN + "/youtubei/v1/"
# key appears to be the same for all unauthenticated users
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"

YT_MUSIC_URI_PREFIX = "https://music.youtube.com/youtubei/v1/search?"

YT_MUSIC_PARAMS = {"alt": "json", "key": "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30"}
YT_MUSIC_HEADERS = {
    "user-agent": USER_AGENT,
    # "accept": "*/*",
    # "accept-encoding": "gzip, deflate",
    # "content-type": "application/json",
    # "content-encoding": "gzip",
    "origin": YT_MUSIC_DOMAIN,
    "referer": YT_MUSIC_DOMAIN,
}

YT_MUSIC_CONTEXT = {
    "client": {"clientName": "WEB_REMIX", "clientVersion": "1." + time.strftime("%Y%m%d", time.gmtime()) + ".01.00"},
}

YT_MUSIC_PAYLOAD_STRING = (
    '{{"context":{{"client":{{"clientName":"WEB_REMIX",'
    '"clientVersion":"0.1"}}}},"query":"{query}",'
    '"params":"Eg-KAQwIARAAGAAgACgAMABqChADEAQQCRAFEAo="}}'
)

Filter: t.TypeAlias = t.Literal[
    "songs", "videos", "albums", "artists", "playlists", "community_playlists", "featured_playlists", "uploads"
]
Scope: t.TypeAlias = t.Literal["library", "uploads"]
TabKey: t.TypeAlias = t.Literal["musicCardShelfRenderer", "musicShelfRenderer"]
ResultType: t.TypeAlias = t.Literal["Song", "Video", "Album"]
Tab: t.TypeAlias = t.Literal["Songs", "Videos", "Albums", "Artists", "Community playlists", "Featured playlists"]

FILTERS: t.Final = (
    "songs",
    "videos",
    "albums",
    "artists",
    "playlists",
    "community_playlists",
    "featured_playlists",
    "uploads",
)
SCOPES: t.Final = ("library", "uploads")
TABS: t.Final = ("Songs", "Videos", "Albums", "Artists", "Community playlists", "Featured playlists")

TOP_RESULT_KEY: t.Final = "musicCardShelfRenderer"
NORMAL_RESULT_KEY: t.Final = "musicShelfRenderer"


def duration_in_seconds(duration_str: str) -> int:
    """
    Converts a duration string to seconds.
    Example: '2:30' -> 150
    """
    if not duration_str:
        return 0

    split = duration_str.split(":")
    split.reverse()

    multipliers = [1, 60, 3600, 3600 * 24]
    duration = 0

    for i, part in enumerate(split):
        duration += int(part) * multipliers[i]

    return duration


def views_as_integer(views: str) -> int:
    """
    Converts a view count string to an integer.
    Example: '1.2M' -> 1_200_000
    """
    if not views:
        return 0

    multipliers: dict[str, int] = {
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000,
    }

    num_string = views[:-1]
    unit_string = views[-1]

    return int(float(num_string) * multipliers[unit_string])


async def search_music(query: str):
    """
    Search YouTube music for a query.
    """

    body = {"context": YT_MUSIC_CONTEXT, "query": query, "params": "EhGKAQ4IARABGAEgASgAOAFAAUICCAE%3D"}

    async with httpx.AsyncClient() as client:
        url = YT_MUSIC_BASE_API + "search"
        resp = await client.post(
            url,
            json=body,
            params=YT_MUSIC_PARAMS,
            headers=YT_MUSIC_HEADERS,
        )

    data = resp.json()

    with open(f"data-{time.time()}.json", "w") as f:
        json.dump(data, f, indent=4)

    if "error" in data:
        raise Exception(data["error"])

    return parse_yt_music_response(data)


def tabs_from_scope(data: dict) -> dict:
    tabs = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]
    return tabs


def video_data_from_nested(title_data: dict, video_data: dict):
    """
    Extracts video data from nested data structures.
    Should be a dict with a key 'run' containing a list of dictionaries.


    title_data example:
    "runs": [
        0: { "text": "Summrs - Back 2 Da Basic [prod.twunuzis] Lyric Video" }
    ]

    video_data example:
    "runs": [
        0: { "text": "Video" },
        1: { "text": " • " },
        2: { "text": "Summrs" },
        3: { "text": " & " },
        4: { "text": "twunuzis" },
        5: { "text": " • " },
        6: { "text": "2.8M views" },
        7: { "text": " • " },
        8: { "text": "2:16 }
    ]
    """

    class Run(t.TypedDict):
        text: str

    class Artist(t.TypedDict):
        name: str

    title: str = title_data["runs"][0]["text"]

    old_runs = video_data["runs"]
    new_runs: list[Run] = []

    for run in old_runs:
        text = run["text"]
        if text.startswith(" ") and text.endswith(" "):
            continue
        new_runs.append(run)

    data = {
        "title": title,
        "video_type": new_runs.pop(0)["text"],
        "duration": duration_in_seconds(new_runs.pop()["text"]),
    }

    views_or_album: str = new_runs.pop()["text"]

    if views_or_album.endswith("views"):
        data["views"] = views_as_integer(views_or_album.removesuffix(" views"))
    else:
        data["album"] = {"name": views_or_album}

    artists: list[Artist] = []

    for run in new_runs:
        text = run["text"]
        artists.append({"name": text})

    data["artists"] = artists

    return data


def song_or_video_id(song_or_video_data: dict) -> str:
    """
    Extracts the video_id from a song or video data object.
    """

    if "playlistItemData" in song_or_video_data:
        return song_or_video_data["playlistItemData"]["videoId"]

    normal_overlay = song_or_video_data.get("overlay")
    thumbnail_overlay = song_or_video_data.get("thumbnailOverlay")

    overlay = normal_overlay or thumbnail_overlay

    if not overlay:
        raise Exception("No overlay found in song or video data.")

    long_key_one = "musicItemThumbnailOverlayRenderer"
    long_key_two = "musicPlayButtonRenderer"

    video_id: str = overlay[long_key_one]["content"][long_key_two]["playNavigationEndpoint"]["watchEndpoint"]["videoId"]
    return video_id


def parse_top_result(top_result_data: dict) -> TopResult:

    navigation_endpoint = top_result_data["title"]["runs"][0]["navigationEndpoint"]
    navigation_endpoint_keys = set(navigation_endpoint.keys())

    mode: t.Literal["watch", "browse"] = "watch" if "watchEndpoint" in navigation_endpoint_keys else "browse"

    mode_endpoint = navigation_endpoint[f"{mode}Endpoint"]
    mode_endpoint_keys = list(mode_endpoint.keys())
    mode_endpoint_key = mode_endpoint_keys[-1]

    next_key = next(iter(mode_endpoint[mode_endpoint_key].keys()))
    last_key = next(iter(mode_endpoint[mode_endpoint_key][next_key].keys()))

    page_type: str = mode_endpoint[mode_endpoint_key][next_key][last_key]

    print(page_type)

    if page_type not in ("MUSIC_VIDEO_TYPE_OMW", "MUSIC_VIDEO_TYPE_ATV"):
        # not a song or video
        return None

    title_data = top_result_data["title"]
    video_data = top_result_data["subtitle"]

    nested_data = video_data_from_nested(title_data, video_data)
    video_id = song_or_video_id(top_result_data)

    if page_type == "MUSIC_VIDEO_TYPE_ATV":
        is_explicit = song_is_explicit(top_result_data)
        return YouTubeMusicSong(**nested_data, video_id=video_id, is_explicit=is_explicit)
    else:  # page_type = "MUSIC_VIDEO_TYPE_OMW"
        return YouTubeMusicVideo(**nested_data, video_id=video_id)


def song_is_explicit(song_or_video_data: dict) -> bool:
    normal_badges: list[dict] | None = song_or_video_data.get("badges")
    subtitle_badges: list[dict] | None = song_or_video_data.get("subtitleBadges")
    badges = normal_badges or subtitle_badges

    if not badges:
        return False

    with contextlib.suppress(KeyError):
        for badge in badges:
            label: str = badge["musicInlineBadgeRenderer"]["accessibilityData"]["accessibilityData"]["label"]
            if label == "Explicit":
                return True

    return False


def parse_song_or_video(song_or_video_data: dict) -> dict:
    long_key = "musicResponsiveListItemRenderer"
    long_key_column = "musicResponsiveListItemFlexColumnRenderer"

    song_or_video_data = song_or_video_data[long_key]

    title_data = song_or_video_data["flexColumns"][0][long_key_column]["text"]
    video_data = song_or_video_data["flexColumns"][1][long_key_column]["text"]

    video_id = song_or_video_id(song_or_video_data)
    # videos don't have this only songs
    is_explicit = song_is_explicit(song_or_video_data)
    nested_data = video_data_from_nested(title_data, video_data)

    return {**nested_data, "video_id": video_id, "is_explicit": is_explicit}


def parse_category(song_or_video_data: dict) -> list[dict] | None:
    category_type: Tab = song_or_video_data["title"]["runs"][0]["text"]

    if category_type not in ("Songs", "Videos"):
        return None

    songs_or_videos = song_or_video_data["contents"]
    return [parse_song_or_video(song_or_video) for song_or_video in songs_or_videos]


def parse_tab(tab: dict) -> list[dict] | dict | None:
    return parse_category(tab[NORMAL_RESULT_KEY])


def is_top_result(tab: dict) -> bool:
    tab_key: TabKey = list(tab.keys())[0]
    return tab_key == TOP_RESULT_KEY


def parse_yt_music_response(data: dict) -> YoutubeMusicSearch:
    if "contents" not in data:
        return YoutubeMusicSearch(top_result=None, songs=[], videos=[])

    if "tabbedSearchResultsRenderer":
        tabs = tabs_from_scope(data)
    else:
        tabs = data["contents"]

    tabs = tabs["sectionListRenderer"]["contents"]

    if not tabs:
        return YoutubeMusicSearch(top_result=None, songs=[], videos=[])

    top_result: TopResult = None

    if is_top_result(tabs[0]):
        top_result = parse_top_result(tabs.pop(0)[TOP_RESULT_KEY])

    return top_result

    # for tab in tabs:
    #     res.append(parse_tab(tab))

    # return res


if __name__ == "__main__":

    # filter_options = [
    #     "songs",
    #     "videos",
    #     "albums",
    #     "artists",
    #     "playlists",
    #     "community_playlists",
    #     "featured_playlists",
    #     "uploads",
    # ]
    # scope_options = ["library", "uploads"]
    # ignore_spelling_options = [True, False]

    # options = itertools.product(filter_options, scope_options, ignore_spelling_options)

    # for option in options:
    #     filter, scope, ignore_spelling = option
    #     rich.print(f"filter: {filter}, scope: {scope}, ignore_spelling: {ignore_spelling}")
    #     rich.print(get_search_params(filter, scope, ignore_spelling))
    #     rich.print(f'[orange]{"-" * 20}[/orange]')

    # {
    # "category": "Songs",
    # "resultType": "song",
    # "videoId": "ZrOKjDZOtkA",
    # "title": "Wonderwall",
    # "artists": [
    #   {
    #     "name": "Oasis",
    #     "id": "UCmMUZbaYdNH0bEd1PAlAqsA"
    #   }
    # ],
    # "album": {
    #   "name": "(What's The Story) Morning Glory? (Remastered)",
    #   "id": "MPREb_9nqEki4ZDpp"
    # },
    # "duration": "4:19",
    # "duration_seconds": 259
    # "isExplicit": false,
    # "feedbackTokens": {
    #   "add": null,
    #   "remove": null
    # }

    async def main() -> None:

        song_title = "Destroy Lonely - Bane"

        ### - my results - ###
        results = await search_music(song_title)
        rich.print(results)

        # ### - ytmusicapi results - ###
        # from ytmusicapi import YTMusic

        # yt = YTMusic()
        # results = yt.search(song_title)
        # results = [r for r in results if r["resultType"] in ("song", "video")]

        # rich.print(results)

    asyncio.run(main())

    # print()
