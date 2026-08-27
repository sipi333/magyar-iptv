import json
import urllib.request
from pathlib import Path

API = "https://iptv-org.github.io/api"
OUTPUT = Path("magyar.m3u")


def get_json(name):
    url = API + "/" + name
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        return json.load(response)


def text(value):
    return str(value or "").lower()


def is_hungarian(feed):
    languages = feed.get("languages", [])
    return "hun" in languages


def is_religious(channel):
    categories = [
        text(x)
        for x in channel.get("categories", [])
    ]

    return "religious" in categories


def is_local(channel, feed):

    names = [
        channel.get("name", ""),
        feed.get("name", "")
    ]

    names += channel.get("alt_names", [])
    names += feed.get("alt_names", [])

    combined = " ".join(
        text(x)
        for x in names
    )

    bad_words = [
        "városi",
        "varosi",
        "helyi",
        "regionális",
        "regionalis",
        "régiós",
        "regios",
        "térségi",
        "tersegi",
        "megyei",
        "kerületi",
        "keruleti",
        "önkormányzati",
        "onkormanyzati",
        "city tv",
        "citytv",
        "local tv",
        "localtv",
        "community tv",
        "országgyűlés",
        "orszaggyules",
        "ogy "
    ]

    for word in bad_words:
        if word in combined:
            return True

    areas = feed.get(
        "broadcast_area",
        []
    )

    for area in areas:

        area = text(area)

        if area.startswith("r/"):
            return True

        if area.startswith("s/"):
            return True

        if area.startswith("ct/"):
            return True

    return False


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

    channels_by_id = {
        c.get("id"): c
        for c in channels
        if c.get("id")
    }

    logos_by_id = {}

    for logo in logos:

        channel_id = logo.get(
            "channel"
        )

        if channel_id:
            logos_by_id[channel_id] = logo.get(
                "url",
                ""
            )

    valid_feeds = []

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

        if not is_hungarian(feed):
            continue

        if is_religious(channel):
            continue

        if is_local(channel, feed):
            continue

        valid_feeds.append(
            feed
        )

    valid_ids = {
        (
            f.get("channel"),
            f.get("id")
        )
        for f in valid_feeds
    }

    best = {}

    for stream in streams:

        key = (
            stream.get("channel"),
            stream.get("feed")
        )

        if key not in valid_ids:
            continue

        url = stream.get("url")

        if not url:
            continue

        channel_id = stream.get(
            "channel"
        )

        quality = stream.get(
            "quality"
        )

        try:
            quality = int(
                quality or 0
            )
        except (TypeError, ValueError):
            quality = 0

        current = best.get(
            channel_id
        )

        if current is None:
            best[channel_id] = (
                quality,
                stream
            )

        elif quality > current[0]:
            best[channel_id] = (
                quality,
                stream
            )

    result = []

    for channel_id, data in best.items():

        channel = channels_by_id.get(
            channel_id
        )

        if not channel:
            continue

        stream = data[1]

        result.append({
            "name": channel.get(
                "name",
                channel_id
            ),
            "id": channel_id,
            "logo": logos_by_id.get(
                channel_id,
                ""
            ),
            "url": stream.get(
                "url"
            )
        })

    result.sort(
        key=lambda x:
        text(x["name"])
    )

    lines = [
        "#EXTM3U"
    ]

    for item in result:

        lines.append(
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

        lines.append(
            item["url"]
        )

    OUTPUT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print(
        "Magyar, nem vallási, "
        "nem helyi csatornák:",
        len(result)
    )

    print(
        "magyar.m3u elkészült."
    )


if __name__ == "__main__":
    main()
