import feedparser
import json
import re
import os
import pathlib
import subprocess
import yt_utils

from typing import Dict, Any
from subprocess import CalledProcessError

BASE_YT_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={0}"


def download_video(feed_video: feedparser.FeedParserDict, dest_path: str) -> None:
    """
    Takes in a video from a channel and downloads it to the location specified
    for that series in the config file.
    ---
    returns both STDOUT and STDERR split on ANSI codes:
        {"stdout": ..., "stderr": ...}
    """
    LOGGER.info(f"Downloading video '{feed_video.title}'")
    try:
        result = subprocess.run(
            yt_utils.BASE_CMD
            + [yt_utils.YTDL_FMT.format(dest_path), feed_video.yt_videoid],
            capture_output=True,
            check=True,
        )
    except CalledProcessError as cpe:
        LOGGER.error("'youtube-dl' command raised a non-zero exit status")
        result = cpe
    yt_utils.log_result(result)


def find_series(
    channel: Dict[str, Any], video: feedparser.FeedParserDict
) -> Dict[str, Any]:
    """
    Match a given video against the list of series we are matching against in the config
    Matches using a regex against the title of the video
    ---
    returns the series config data if the title matches, otherwise nothing
    """
    for series in channel["series_to_check"]:
        if re.match(series["title_format"], video.title):
            LOGGER.info(f"Found match for '{video.title}' :: '{series['folder']}'")
            return series


def process_channel(channel: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the latest videos from a channel's RSS feed and parse them
    If a video is new and matches desired series title formats, download and store it
    ---
    returns the channel after its update (including skipped/downloaded IDs)
    """
    LOGGER.info(f"Processing channel '{channel['name']}'")
    feed = feedparser.parse(BASE_YT_URL.format(channel["id"]))
    processed = channel["checked_ids"]["skipped"] + channel["checked_ids"]["downloaded"]
    videos_to_check = [v for v in feed.entries if v.yt_videoid not in processed]
    LOGGER.info(
        f"Checking a total of {len(videos_to_check)} new videos from '{channel['name']}' feed"
    )
    for video in videos_to_check:
        LOGGER.info(f"Checking {video.title}")
        series = find_series(channel, video)
        if not series:
            LOGGER.info(
                f"No series found for '{video.title}' -- adding '{video.yt_videoid}' to skipped"
            )
            channel["checked_ids"]["skipped"].append(video.yt_videoid)
            continue
        # Create the series folder if it doesn't already exist
        folder = os.path.join(yt_utils.BASE_SHARE, channel["name"], series["folder"])
        pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
        download_video(video, folder)
        channel["checked_ids"]["downloaded"].append(video.yt_videoid)
    return channel


if __name__ == "__main__":
    LOGGER = yt_utils.config_logger(log_file="yt-cache.log")
    cfg_file = os.path.join(yt_utils.BASE_SHARE, "channels.json")
    with open(cfg_file, "r") as f:
        channels = json.load(fp=f)
    updated_channels = [process_channel(channel) for channel in channels]
    with open(cfg_file, "w") as f:
        json.dump(obj=updated_channels, fp=f, indent=4)
