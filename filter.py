import json
import urllib.request
from pathlib import Path

API = "https://iptv-org.github.io/api"

OUTPUT = Path("magyar.m3u")


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        return json.load(response)


def get_quality(value):
    if not value:
        return 0

    digits = "".join(
        character
        for character in str(value)
        if character.isdigit()
    )

    if not digits:
        return 0

    return int(digits)


def main():

    print("IPTV-org API letöltése...")

    channels = get_json(
        f"{API}/channels.json"
    )

    feeds = get_json(
        f"{API}/feeds.json"
    )

    streams = get_json(
        f"{API}/streams.json"
    )

    logos = get_json(
        f"{API}/logos.json"
    )

    print(
        "Csatornák:",
        len(channels)
    )

    print(
        "Feedek:",
        len(feeds)
    )

    print(
        "Streamek:",
        len(streams)
    )

    channels_by_id = {
        channel["id"]: channel
        for channel in channels
        if channel.get("id")
    }

    logos_by_channel = {}

    for logo in logos:

        channel_id = logo.get("channel")

        if not channel_id:
            continue

        if channel_id not in logos_by_channel:
            logos_by_channel[channel_id] = logo

        elif logo.get("in_use") is True:
            logos_by_channel[channel_id] = logo

    valid_feeds = []

    for feed in feeds:

        channel_id = feed.get("channel")

        if not channel_id:
            continue

        channel = channels_by_id.get(
            channel_id
        )

        if not channel:
            continue

        # Csak magyarországi csatorna
        if channel.get("country") != "HU":
            continue

        # Vallási kategória kizárása
        categories
