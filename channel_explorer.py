import subprocess
import requests
import os
import sys
import yt_utils
import json

from bullet import Bullet, ScrollBar, Input, YesNo
from typing import Union, List


class Playlist:
    def __init__(self, *, id: str, title: str):
        self.id = id
        self.title = title

    def __str__(self):
        return f"Playlist(id='{self.id}', title='{self.title}'"


class Video:
    def __init__(self, *, id: str, title: str, pos: int, video_id: str):
        self.id = video_id
        self.playlist_id = id
        self.title = title
        self.position = pos

    def __str__(self):
        return f"Video[{self.position}](id='{self.id}', title='{self.title}')"


class Details:
    def __init__(self, *, total: str, count: int, next_page: str, prev_page: str):
        self.total = total
        self.count = count
        self.next_page = next_page
        self.prev_page = prev_page
        self.items: List[Union[Playlist, Video]] = []

    def __str__(self):
        return (
            "Details:\n"
            f"\tTotal: {self.total}, Count: {self.count}\n"
            f"\tItems:\n"
            f"\t\t" + "\n\t\t".join([str(i) for i in self.items])
        )


def get_playlists(
    *, channel_id: str = "", playlist_id: str = "", page: str = ""
) -> Details:
    params = {
        "key": yt_utils.API_KEY,
        "part": "id,contentDetails,snippet",
        "maxResults": 100,
        "pageToken": page,
    }
    if playlist_id != "":
        params["id"] = playlist_id
    else:
        params["channelId"] = channel_id
    results = requests.get(
        url=yt_utils.BASE_URL.format("playlists"),
        params=params,
        headers={"Content-type": "application/json"},
    ).json()
    details = Details(
        total=results["pageInfo"]["totalResults"],
        count=results["pageInfo"]["resultsPerPage"],
        next_page=results.get("nextPageToken", ""),
        prev_page=results.get("prevPageToken", ""),
    )
    for item in results["items"]:
        details.items.append(Playlist(id=item["id"], title=item["snippet"]["title"]))
    return details


def get_videos(*, playlist_id: str = "", video_id: str = "", page: str = "") -> Details:
    params = {
        "key": yt_utils.API_KEY,
        "part": "id,contentDetails,snippet",
        "maxResults": 50,
        "pageToken": page,
    }
    if video_id != "":
        params["videoId"] = video_id
    else:
        params["playlistId"] = playlist_id
    results = requests.get(
        url=yt_utils.BASE_URL.format("playlistItems"),
        params=params,
        headers={"Content-type": "application/json"},
    ).json()
    details = Details(
        total=results["pageInfo"]["totalResults"],
        count=results["pageInfo"]["resultsPerPage"],
        next_page=results.get("nextPageToken", ""),
        prev_page=results.get("prevPageToken", ""),
    )
    for item in results["items"]:
        details.items.append(
            Video(
                id=item["id"],
                title=item["snippet"]["title"],
                pos=item["snippet"]["position"],
                video_id=item["snippet"]["resourceId"]["videoId"],
            )
        )
    return details


def playlist_prompt(channel_id: str, page_token: str = ""):
    playlists = get_playlists(channel_id=channel_id, page=page_token)
    pl_choices = []
    if playlists.prev_page != "":
        pl_choices.append("[Previous Page]")
    pl_choices = pl_choices + [p.title for p in playlists.items]
    if playlists.next_page != "":
        pl_choices.append("[Next Page]")
    return playlists, ScrollBar(
        "Select a Playlist:",
        height=10,
        pointer="→ ",
        align=4,
        margin=1,
        choices=pl_choices,
    )


def video_prompt(playlist_id: str, page_token: str = ""):
    videos = get_videos(playlist_id=playlist_id, page=page_token)
    v_choices = ["[Range]", "[ALL VIDEOS]"]
    if videos.prev_page != "":
        v_choices.append("[Previous Page]")
    v_choices = v_choices + [v.title for v in videos.items]
    if videos.next_page != "":
        v_choices.append("[Next Page]")
    return videos, ScrollBar(
        "Select a Video:", height=10, pointer="→ ", align=4, margin=1, choices=v_choices
    )


def clear():
    sys.stdout.write("\u001b[2J")


if __name__ == "__main__":
    LOGGER = yt_utils.config_logger(log_file="yt-channels.log")
    with open(os.path.join(yt_utils.BASE_SHARE, "channels.json"), "r") as cf:
        channels = {c["name"]: c["id"] for c in json.load(fp=cf)}
    ch = Bullet(
        "Select a Channel:",
        bullet="→ ",
        align=4,
        margin=1,
        choices=list(channels.keys()),
    )
    clear()
    channel = ch.launch()
    cp = Input(f"Enter a folder name ({channel}): ", default=channel)
    c_folder = cp.launch()
    details, plp = playlist_prompt(channels[channel])
    clear()
    title = plp.launch()
    while title in ["[Next Page]", "[Previous Page]"]:
        page = details.next_page if title == "[Next Page]" else details.prev_page
        details, plp = playlist_prompt(channels[channel], page)
        clear()
        title = plp.launch()
    playlist = [pl for pl in details.items if pl.title == title][0]
    fp = Input(f"Enter a folder name ({playlist.title}): ", default=playlist.title)
    f_folder = fp.launch()
    addp = YesNo(
        prompt="Add this playlist to be monitored? (y/N)", default="N", prompt_prefix=""
    )
    should_monitor = addp.launch()
    if should_monitor:
        regp = Input(
            prompt="What should the regex be for the videos in this playlist?\n"
        )
        reg = regp.launch()
        cfg_path = os.path.join(yt_utils.BASE_SHARE, "channels.json")
        with open(cfg_path, "r") as inf:
            current_cfg = json.load(fp=inf)
        for i in range(len(current_cfg)):
            if current_cfg[i]["name"] != channel:
                continue
            current_cfg[i]["series_to_check"].append(
                {"folder": f_folder, "title_format": reg}
            )
        with open(cfg_path, "w") as outf:
            json.dump(current_cfg, fp=outf, indent=4)
    details, vp = video_prompt(playlist.id)
    clear()
    video = vp.launch()
    cmd = yt_utils.BASE_CMD + [
        yt_utils.YTDL_FMT.format(os.path.join(yt_utils.BASE_SHARE, c_folder, f_folder)),
    ]
    while video in ["[Next Page]", "[Previous Page]"]:
        page = details.next_page if playlist == "[Next Page]" else details.prev_page
        details, vp = video_prompt(playlist.id, page)
        clear()
        video = vp.launch()
    if video == "[Range]":
        ri = Input("Enter a 1-indexed range ([start],[count]): ", strip=True)
        range_input = ri.launch().split(",")
        start = int(range_input[0])
        count = int(range_input[1])
        count = details.total if count > details.total else count
        start = start if start > 0 else 1
        item_spec = f"{start}-{count + start}"
        cmd += ["--playlist-items", item_spec, playlist.id]
    elif video == "[ALL VIDEOS]":
        video_ids = "ALL"
        cmd.append(playlist.id)
    else:
        video_id = [v.id for v in details.items if v.title == video][0]
        cmd.append(video_id)
    # RUN COMMAND
    try:
        LOGGER.info("Executing " + " ".join(cmd))
        print(f"Downloading video(s) from the {channel} playlist '{playlist.title}'...")
        print("(This may take a very long time!)")
        result = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as cpe:
        LOGGER.error("'youtube-dl' command raised a non-zero exit status")
        result = cpe
    print(
        "Finished downloading video(s)!  Check "
        f"{os.path.join(yt_utils.BASE_SHARE, 'yt-get.log')}"
        "for details"
    )
    yt_utils.log_result(result)
