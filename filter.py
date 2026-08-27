import json
import urllib.request
from pathlib import Path

API = "https://iptv-org.github.io/api"
OUTPUT = Path("magyar.m3u")

# Olyan csatornaazonosítók, amelyek rövid nevük miatt
# külön kizárást igényelnek.
EXCLUDE_IDS = {
    "BTV.hu",
}

# Kizárt kategóriák.
EXCLUDE_CATEGORIES = {
    "religious",
    "radio",
}


def get_json(filename):
    url = API + "/" + filename

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        return json.load(response)


def is_hungarian(feed):
    return "hun" in feed.get("languages", [])


def is_countrywide(feed):
    areas = feed.get("broadcast_area", [])

    return "c/HU" in areas


def is_local_or_regional(feed):
    areas = feed.get("broadcast_area", [])

    for area in areas:
        if (
            area.startswith("r/")
            or area.startswith("s/")
            or area.startswith("ct/")
        ):
            return True

    return False


def contains_local_words(channel, feed):
    values = []

    values.append(channel.get("name", ""))
    values.extend(channel.get("alt_names", []))
    values.append(feed.get("name", ""))
    values.extend(feed.get("alt_names", []))

    text = " ".join(
        str(x).lower()
        for x in values
    )

    words = [
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
        "kerületi tv",
        "keruleti tv",
        "önkormányzati tv",
        "onkormanyzati tv",
        "local tv",
        "localtv",
        "city tv",
        "citytv",
        "community tv",
        "közösségi tv",
        "kozossegi tv",
    ]

    return any(
        word in text
        for word in words
    )


def stream_quality(stream):
    quality = str(
        stream.get("quality") or ""
    )

    digits = "".join(
        c for c in quality
        if c.isdigit()
    )

    return int(digits or 0)


def main():

    print("IPTV-org adatok letöltése...")

    channels = get_json(
        "channels.json"
    )

    feeds = get_json(
        "feeds.json"
    )

    streams = get_json(
        "streams.json"
    )

    logos = get_json(
        "logos.json"
    )

    channel_map = {
        channel["id"]: channel
        for channel in channels
        if channel.get("id")
    }

    logo_map = {}

    for logo in logos:

        channel_id = logo.get(
            "channel"
        )

        if not channel_id:
            continue

        if (
            logo.get("in_use")
            or channel_id not in logo_map
        ):
            logo_map[channel_id] = logo.get(
                "url",
                ""
            )

    valid_feeds = {}

    for feed in feeds:

        channel_id = feed.get(
            "channel"
        )

        if not channel_id:
            continue

        if channel_id in EXCLUDE_IDS:
            continue

        channel = channel_map.get(
            channel_id
        )

        if not channel:
            continue

        if channel.get(
            "country"
        ) != "HU":
            continue

        if not is_hungarian(feed):
            continue

        categories = set(
            channel.get(
                "categories",
                []
            )
        )

        if categories.intersection(
            EXCLUDE_CATEGORIES
        ):
            continue

        if is_local_or_regional(feed):
            continue

        if contains_local_words(
            channel,
            feed
        ):
            continue

        # Országos feed.
        if not is_countrywide(feed):
            continue

        old = valid_feeds.get(
            channel_id
        )

        # Ha több országos feed van,
        # az is_main legyen az elsődleges.
        if old is None:
            valid_feeds[channel_id] = feed

        elif feed.get("is_main"):
            valid_feeds[channel_id] = feed

    print(
        "Megfelelő magyar országos feedek:",
        len(valid_feeds)
    )

    best_stream = {}

    for stream in streams:

        channel_id = stream.get(
            "channel"
        )

        feed_id = stream.get(
            "feed"
        )

        if channel_id not in valid_feeds:
            continue

        selected_feed = valid_feeds[
            channel_id
        ]

        if feed_id != selected_feed.get(
            "id"
        ):
            continue

        url = stream.get("url")

        if not url:
            continue

        quality = stream_quality(
            stream
        )

        old = best_stream.get(
            channel_id
        )

        if (
            old is None
            or quality > old[0]
        ):
            best_stream[channel_id] = (
                quality,
                stream
            )

    result = []

    for channel_id, data in best_stream.items():

        channel = channel_map.get(
            channel_id
        )

        if not channel:
            continue

        stream = data[1]

        result.append({
            "id": channel_id,
            "name": channel.get(
                "name",
                channel_id
            ),
            "logo": logo_map.get(
                channel_id,
                ""
            ),
            "url": stream.get(
                "url"
            ),
            "referrer": stream.get(
                "referrer"
            ),
            "user_agent": stream.get(
                "user_agent"
            )
        })

    result.sort(
        key=lambda item:
        item["name"].lower()
    )

    output = [
        "#EXTM3U"
    ]

    for item in result:

        line = (
            '#EXTINF:-1 '
            'tvg-country="HU" '
            'tvg-language="Hungarian" '
            'tvg-id="' +
            item["id"] +
            '" '
            'tvg-logo="' +
            item["logo"] +
            '",' +
            item["name"]
        )

        output.append(line)

        if item["referrer"]:
            output.append(
                "#EXTVLCOPT:http-referrer="
                + item["referrer"]
            )

        if item["user_agent"]:
            output.append(
                "#EXTVLCOPT:http-user-agent="
                + item["user_agent"]
            )

        output.append(
            item["url"]
        )

    OUTPUT.write_text(
        "\n".join(output) + "\n",
        encoding="utf-8"
    )

    print(
        "Létrehozott csatornák:",
        len(result)
    )

    print(
        "magyar.m3u elkészült."
    )


if __name__ == "__main__":
    main()
