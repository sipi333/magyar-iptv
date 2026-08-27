import json
import urllib.request
from pathlib import Path

API = "https://iptv-org.github.io/api"
OUTPUT = Path("magyar.m3u")


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def norm(value):
    return str(value or "").strip().lower()


def quality(value):
    digits = "".join(
        c for c in str(value or "")
        if c.isdigit()
    )
    return int(digits) if digits else 0


def religious(channel):
    categories = {
        norm(x)
        for x in channel.get("categories", [])
    }
    return "religious" in categories


def local_feed(feed):
    areas = {
        norm(x)
        for x in feed.get("broadcast_area", [])
    }

    if "c/hu" not in areas:
        return True

    for area in areas:
        if area.startswith("r/"):
            return True
        if area.startswith("s/"):
            return True
        if area.startswith("ct/"):
            return True

    return False


def local_name(channel, feed):

    names = [
        channel.get("name", ""),
        feed.get("name", "")
    ]

    names += channel.get(
        "alt_names", []
    )

    names += feed.get(
        "alt_names", []
    )

    bad = [
        "városi tv",
        "varosi tv",
        "városi televízió",
        "varosi televizio",
        "helyi tv",
        "helyi televízió",
        "helyi televizio",
        "regionális tv",
        "regionalis tv",
        "régiós tv",
        "regios tv",
        "térségi tv",
        "tersegi tv",
        "megyei tv",
        "megyei televízió",
        "megyei televizio",
        "kerületi tv",
        "keruleti tv",
        "önkormányzati tv",
        "onkormanyzati tv",
        "local tv",
        "community tv"
    ]

    for name in names:
        name = norm(name)

        for word in bad:
            if word in name:
                return True

    return False


def main():

    print("IPTV-org API letöltése...")

    channels = get_json(
        API + "/channels.json"
    )

    feeds = get_json(
        API + "/feeds.json"
    )

    streams = get_json(
        API + "/streams.json"
    )

    logos = get_json(
        API + "/logos.json"
    )

    channels_by_id = {
        c["id"]: c
        for c in channels
        if c.get("id")
    }

    logos_by_channel = {}

    for logo in logos:

        channel_id = logo.get(
            "channel"
        )

        if not channel_id:
            continue

        if (
            channel_id
            not in logos_by_channel
        ):
            logos_by_channel[
                channel_id
            ] = logo

        elif logo.get("in_use"):

            logos_by_channel[
                channel_id
            ] = logo

    valid = []

    for feed in feeds:

        channel_id = feed.get(
            "channel"
        )

        if not channel_id:
            continue

        channel = channels_by_id.get(
            channel_id
        )

        if not channel:
            continue

        if channel.get(
            "country"
        ) != "HU":
            continue

        if religious(channel):
            continue

        languages = {
            norm(x)
            for x in feed.get(
                "languages",
                []
            )
        }

        if "hun" not in languages:
            continue

        if local_feed(feed):
            continue

        if local_name(
            channel,
            feed
        ):
            continue

        valid.append(feed)

    print(
        "Megfelelő magyar országos feedek:",
        len(valid)
    )

    valid_keys = {
        (
            f.get("channel"),
            f.get("id")
        )
        for f in valid
    }

    streams_by_feed = {}

    for stream in streams:

        key = (
            stream.get("channel"),
            stream.get("feed")
        )

        if key not in valid_keys:
            continue

        if not stream.get("url"):
            continue

        streams_by_feed.setdefault(
            key,
            []
        ).append(stream)

    result = {}

    for feed in valid:

        channel_id = feed.get(
            "channel"
        )

        feed_id = feed.get(
            "id"
        )

        channel = channels_by_id.get(
            channel_id
        )

        available = streams_by_feed.get(
            (
                channel_id,
                feed_id
            ),
            []
        )

        if not channel:
            continue

        if not available:
            continue

        available.sort(
            key=lambda x:
            -quality(
                x.get("quality")
            )
        )

        stream = available[0]

        name = str(
            channel.get(
                "name",
                channel_id
            )
        )

        logo = ""

        if channel_id in logos_by_channel:

            logo = str(
                logos_by_channel[
                    channel_id
                ].get(
                    "url",
                    ""
                )
            )

        item = {
            "id": channel_id,
            "name": name,
            "logo": logo,
            "url": str(
                stream.get("url")
            ),
            "referrer": str(
                stream.get(
                    "referrer"
                ) or ""
            ),
            "user_agent": str(
                stream.get(
                    "user_agent"
                ) or ""
            ),
            "quality": quality(
                stream.get("quality")
            )
        }

        old = result.get(
            channel_id
        )

        if old is None:
            result[channel_id] = item

        elif item["quality"] > old["quality"]:
            result[channel_id] = item

    items = list(
        result.values()
    )

    items.sort(
        key=lambda x:
        norm(x["name"])
    )

    print(
        "Végleges csatornák:",
        len(items)
    )

    lines = [
        "#EXTM3U"
    ]

    for item in items:

        name = item["name"].replace(
            '"',
            "'"
        )

        channel_id = item["id"].replace(
            '"',
            "'"
        )

        logo = item["logo"].replace(
            '"',
            "'"
        )

        lines.append(
            '#EXTINF:-1 '
            f'tvg-id="{channel_id}" '
            f'tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            f'group-title="Magyarorszag",{name}'
        )

        if item["referrer"]:
            lines.append(
                "#EXTVLCOPT:http-referrer="
                + item["referrer"]
            )

        if item["user_agent"]:
            lines.append(
                "#EXTVLCOPT:http-user-agent="
                + item["user_agent"]
            )

        lines.append(
            item["url"]
        )

    OUTPUT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print(
        "magyar.m3u elkészült."
    )


if __name__ == "__main__":
    main()
