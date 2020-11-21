import json
import re
import sys
import os
import requests
import yt_utils

CHANNEL_REGEX = re.compile(r"https://www.youtube.com/channel/(.*)")


if __name__ == "__main__":
    match = None
    while not match:
        url = input("Paste the channel URL here:  ")
        match = CHANNEL_REGEX.match(url)
    channel_id: str = match.groups()[0]
    result = requests.get(
        url=yt_utils.BASE_URL.format("channels"),
        params={
            "key": yt_utils.API_KEY,
            "part": "snippet",
            "maxResults": 1,
            "id": channel_id,
        },
        headers={"Content-type": "application/json"},
    ).json()
    if "items" not in result:
        print(f"ERROR: Could not find a channel with the ID '{channel_id}'")
        sys.exit(1)
    channel_name = result["items"][0]["snippet"]["title"]
    cfg_path = os.path.join(yt_utils.BASE_SHARE, "channels.json")
    with open(cfg_path, "r") as inf:
        current_cfg = json.load(fp=inf)
    ids = [c["id"] for c in current_cfg]
    if channel_id in ids:
        print(
            f"ERROR: The channel ID '{channel_id}' already exists in 'channels.json'!"
        )
        sys.exit(1)
    current_cfg.append(
        {
            "id": channel_id,
            "name": channel_name,
            "checked_ids": {"skipped": [], "downloaded": []},
            "series_to_check": [],
        }
    )
    with open(cfg_path, "w") as outf:
        json.dump(current_cfg, fp=outf, indent=4)
    print(f"Added '{channel_name}' ({channel_id}) to the 'channels.json' config!")
    print(
        f"Config file located at [{os.path.join(yt_utils.BASE_SHARE, 'channels.json')}]."
    )
