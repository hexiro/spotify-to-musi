from ytmusicapi import YTMusic
from spotify_to_musi.main import search_youtube_for_track
from spotify_to_musi.typings.core import Track

ytmusic = YTMusic()

track = Track(artist="Trippie Redd", song="Demon Time (feat. Ski Mask The Slump God)", spotify_duration=159)

def test_transfer() -> None:
    track_Data = search_youtube_for_track(track, ytmusic)
    assert track_Data is not None
    assert track_Data.video_id == "O1zpcGTL3FI"
    