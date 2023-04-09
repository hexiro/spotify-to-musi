import asyncio
import contextlib
import time
import httpx
import typing as t
import rich


from typings.youtube import YouTubeMusicSearch, YouTubeMusicSong, YouTubeMusicVideo, YouTubeMusicResult


YT_MUSIC_DOMAIN = "https://music.youtube.com"
YT_MUSIC_BASE_API = YT_MUSIC_DOMAIN + "/youtubei/v1/"
# key appears to be the same for all unauthenticated users
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"


YT_MUSIC_PARAMS = {"alt": "json", "key": "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30"}
YT_MUSIC_HEADERS = {
    "user-agent": USER_AGENT,
    "origin": YT_MUSIC_DOMAIN,
    "referer": YT_MUSIC_DOMAIN,
}

YT_MUSIC_CONTEXT = {
    "client": {"clientName": "WEB_REMIX", "clientVersion": "1." + time.strftime("%Y%m%d", time.gmtime()) + ".01.00"},
}


CategoryKey: t.TypeAlias = t.Literal["musicCardShelfRenderer", "musicShelfRenderer", "itemSectionRenderer"]
Category: t.TypeAlias = t.Literal["Songs", "Videos", "Albums", "Artists", "Community playlists", "Featured playlists"]

CATEGORIES: t.Final = ("Songs", "Videos", "Albums", "Artists", "Community playlists", "Featured playlists")
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

    if not unit_string.isalpha():
        return int(views.replace(",", ""))

    return int(float(num_string) * multipliers[unit_string])


async def search_music(query: str) -> YouTubeMusicSearch | None:
    """
    Search YouTube music for a query.
    """

    body = {"context": YT_MUSIC_CONTEXT, "query": query}

    async with httpx.AsyncClient() as client:
        url = YT_MUSIC_BASE_API + "search"
        resp = await client.post(
            url,
            json=body,
            params=YT_MUSIC_PARAMS,
            headers=YT_MUSIC_HEADERS,
        )

    data = resp.json()

    # with open(f"data-{time.time()}.json", "w") as f:
    #     json.dump(data, f, indent=4)

    if "error" in data:
        raise Exception(data["error"])

    return parse_yt_music_response(data)


def tabs_from_scope(data: dict) -> dict:
    tabs = data["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]
    return tabs


def parse_title_and_subtitle_data(title_data: dict, video_data: dict):
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
        navigationEndpoint: t.NotRequired[t.Any]

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

    # category_type like "Songs" or "Videos"
    # not important so just remove to get it out of the way.
    # if that isn't first an Artist will be which has a navigationEndpoint to get to their page.
    if "navigationEndpoint" not in new_runs[0]:
        new_runs.pop(0)

    data = {
        "title": title,
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

    data["artists"] = tuple(artists)

    return data


def parse_video_id(song_or_video_data: dict) -> str:
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


def parse_top_result(top_result_data: dict) -> YouTubeMusicResult | None:
    navigation_endpoint = top_result_data["title"]["runs"][0]["navigationEndpoint"]

    # artist
    page_type: str | None = None
    with contextlib.suppress(KeyError):
        long_key_one = "browseEndpointContextSupportedConfigs"
        lone_key_two = "browseEndpointContextMusicConfig"
        page_type = navigation_endpoint["browseEndpoint"][long_key_one][lone_key_two]["pageType"]
    with contextlib.suppress(KeyError):
        long_key_one = "watchEndpointMusicSupportedConfigs"
        lone_key_two = "watchEndpointMusicConfig"
        page_type = navigation_endpoint["watchEndpoint"][long_key_one][lone_key_two]["musicVideoType"]

    if not page_type:
        # page_type not found
        return None

    if page_type not in ("MUSIC_VIDEO_TYPE_OMW", "MUSIC_VIDEO_TYPE_OMV", "MUSIC_VIDEO_TYPE_ATV"):
        # not a song or video
        return None

    title_data = top_result_data["title"]
    video_data = top_result_data["subtitle"]

    title_and_subtitle_data = parse_title_and_subtitle_data(title_data, video_data)
    video_id = parse_video_id(top_result_data)

    if page_type == "MUSIC_VIDEO_TYPE_ATV":
        is_explicit = is_song_explicit(top_result_data)
        return YouTubeMusicSong(**title_and_subtitle_data, video_id=video_id, is_explicit=is_explicit)
    else:  # page_type = "MUSIC_VIDEO_TYPE_OMW"
        return YouTubeMusicVideo(**title_and_subtitle_data, video_id=video_id)


def is_song_explicit(song_or_video_data: dict) -> bool:
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


def parse_song_or_video(song_or_video_data: dict) -> YouTubeMusicSong | YouTubeMusicVideo:
    title_and_subtitle_data = parse_song_or_video_title_and_subtitle_data(song_or_video_data)
    video_id = parse_video_id(song_or_video_data)

    is_song = "album" in title_and_subtitle_data

    if is_song:
        is_explicit = is_song_explicit(song_or_video_data)
        return YouTubeMusicSong(**title_and_subtitle_data, video_id=video_id, is_explicit=is_explicit)

    # is video
    return YouTubeMusicVideo(**title_and_subtitle_data, video_id=video_id)


def parse_song_or_video_title_and_subtitle_data(song_or_video_data: dict) -> dict:
    long_key = "musicResponsiveListItemFlexColumnRenderer"

    title_data = song_or_video_data["flexColumns"][0][long_key]["text"]
    video_data = song_or_video_data["flexColumns"][1][long_key]["text"]

    title_and_subtitle_data = parse_title_and_subtitle_data(title_data, video_data)
    return title_and_subtitle_data


def parse_category(song_or_video_data: dict) -> list[YouTubeMusicSong | YouTubeMusicVideo] | None:
    song_or_video_data = song_or_video_data[NORMAL_RESULT_KEY]

    category_type: Category = song_or_video_data["title"]["runs"][0]["text"]

    if category_type not in ("Songs", "Videos"):
        return None

    contents = song_or_video_data["contents"]
    long_key = "musicResponsiveListItemRenderer"

    results: list[YouTubeMusicSong | YouTubeMusicVideo] = []

    # i don't understand why but occasionally a video will show up in the songs section,
    # so it's safer to just check ourselves and not rely on the categories for the filtering 100%

    for content in contents:
        content = content[long_key]
        results.append(parse_song_or_video(content))

    return results


def is_top_result(tab: dict) -> bool:
    tab_key: CategoryKey = list(tab.keys())[0]
    return tab_key == TOP_RESULT_KEY


def parse_yt_music_response(data: dict) -> YouTubeMusicSearch | None:
    if "contents" not in data:
        return None

    if "tabbedSearchResultsRenderer":
        categories = tabs_from_scope(data)
    else:
        categories = data["contents"]

    categories = categories["sectionListRenderer"]["contents"]

    if not categories:
        return None

    top_result: YouTubeMusicResult | None = None

    songs: list[YouTubeMusicSong] = []
    videos: list[YouTubeMusicVideo] = []

    for category in categories:
        key: CategoryKey = list(category.keys())[0]

        # skip all 'informational' categories
        # they will say things like 'Did you mean: <song name>'
        if key not in (NORMAL_RESULT_KEY, TOP_RESULT_KEY):
            continue

        if is_top_result(category):
            top_result = parse_top_result(category[TOP_RESULT_KEY])
            continue

        category_data = parse_category(category)

        if not category_data:
            continue

        for song_or_video in category_data:
            if isinstance(song_or_video, YouTubeMusicSong):
                songs.append(song_or_video)
            else:
                videos.append(song_or_video)

    return YouTubeMusicSearch(
        top_result=top_result,
        songs=songs,
        videos=videos,
    )


if __name__ == "__main__":

    async def main() -> None:
        song_title = "Destroy Lonely - Bane"
        results = await search_music(song_title)
        rich.print(results)

    async def test() -> None:
        # spelt wrong on purpose
        queries: list[str] = [
            "Destory Lonely - JETLGGD",
            "Destory Lonely - BERGDORF",
            "Destory Lonely - <3MYGNG",
            "Destory Lonely - VTMNTSCOAT",
            "Destory Lonely - NOSTYLIST",
            "Destory Lonely - FAKENGGAS",
            "Destory Lonely - SOARIN",
            "Destory Lonely - TURNINUP",
            "Destory Lonely - LNLY",
            "Destory Lonely - PRSSURE",
            "Destory Lonely - ONTHETABLE",
            "Destory Lonely - SWGSKOOL",
            "Destory Lonely - CRYSTLCSTLES",
            "Destory Lonely - DANGEROUS",
            "Destory Lonely - MKEITSTOP",
            "Destory Lonely - ONTHEFLOOR",
            "Destory Lonely - PASSAROUND",
            "Destory Lonely - OTW",
            "Destory Lonely - VETERAN (feat. Ken Carson)",
        ]

        tasks: list[asyncio.Task[YouTubeMusicSearch | None]] = []

        for query in queries:
            tasks.append(asyncio.create_task(search_music(query)))

        results: list[YouTubeMusicSearch | None] = await asyncio.gather(*tasks) # type: ignore
        results: list[YouTubeMusicSearch] = [r for r in results if r is not None]
        top_results = [r.top_result for r in results]

        rich.print(top_results)

    asyncio.run(test())
