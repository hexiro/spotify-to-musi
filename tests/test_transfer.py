import pytest

from ytmusicapi import YTMusic
from spotify_to_musi.main import search_youtube_for_track
from spotify_to_musi.typings.core import Track

ytmusic = YTMusic()

track_to_expected_video_id: dict[Track, str] = {
    Track(artist="Trippie Redd", song="Demon Time (feat. Ski Mask The Slump God)", spotify_duration=159): "uoyaDo9B5Eo",
    Track(artist="$NOT", song="Doja", spotify_duration=171): "lxfljkiR5Xc",
    Track(artist="Lil Uzi Vert", song="Do What I Want", spotify_duration=175): "ra1cvbdYhps",
    Track(artist="Lil Uzi Vert", song="Erase Your Social", spotify_duration=199): "X21M7w6IkoM",
    Track(artist="Offset", song="How Did I Get Here (feat. J. Cole)", spotify_duration=276): "v8PRzHXYcII",
    Track(artist="Baby Keem", song="ORANGE SODA", spotify_duration=129): "PTv7cJjNig8"
}


@pytest.mark.parametrize("track,expected_video_id", track_to_expected_video_id.items())
def test_transfer(track: Track, expected_video_id: str) -> None:
    track_Data = search_youtube_for_track(track, ytmusic)
    assert track_Data is not None
    assert track_Data.video_id == expected_video_id
