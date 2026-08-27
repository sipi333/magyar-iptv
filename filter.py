import json
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT = Path("magyar.m3u")

API = "https://iptv-org.github.io/api"

# Néhány problémás, rövid azonosító külön kizárása.
EXCLUDE_IDS = {
    "BTV.hu",
}

# Ezeket a kategóriákat nem szeretnénk.
EXCLUDE_CATEGORIES = {
    "religious",
    "radio",
}


def download(url):
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
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def get_json(name):
    return json.loads(
        download(API + "/" + name)
    )


def parse_m3u(text):
    entries = []
    current = None

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current = {
                "info": line,
                "url": None,
            }

        elif (
            current is not None
            and not line.startswith("#")
        ):
            current["url"] = line
            entries.append(current)
            current = None

    return entries


def get_attr(line, name):
    marker = name + '="'

    start = line.find(marker)

    if start == -1:
        return ""

    start += len(marker)

    end = line.find('"', start)

    if end == -1:
        return ""

    return line[start:end]


def is_local_area(feed):
    areas = feed.get(
        "broadcast_area",
        []
    )

    for area in areas:
        if (
            area.startswith("r/")
            or area.startswith("s/")
            or area.startswith("ct/")
        ):
            return True

    return False


def is_hungarian_feed(feed):
    languages = feed.get(
        "languages",
        []
    )

    return "hun" in languages


def is_countrywide(feed):
    return "c/HU" in feed.get(
        "broadcast_area",
        []
    )


def local_name_check(channel, feed):
    text_parts = []

    text_parts.append(
        channel.get("name", "")
    )

    for name in channel.get(
        "alt_names",
        []
    ):
        text_parts.append(name)

    text_parts.append(
        feed.get("name", "")
    )

    text = " ".join(
        str(x).lower()
        for x in text_parts
    )

    # Általános helyi/önkormányzati jelölések.
    bad_phrases = (
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
        "city tv",
        "citytv",
        "local tv",
        "localtv",
    )

    return any(
        phrase in text
        for phrase in bad_phrases
    )


def main():

    print("IPTV-org index.m3u letöltése...")

    playlist_text = download(
        SOURCE
    )

    entries = parse_m3u(
        playlist_text
    )

    print(
        "Indexben talált bejegyzések:",
        len(entries)
    )

    print("IPTV-org API adatok letöltése...")

    channels = get_json(
        "channels.json"
    )

    feeds = get_json(
        "feeds.json"
    )

    logos = get_json(
        "logos.json"
    )

    channel_map = {
        item["id"]: item
        for item in channels
        if item.get("id")
    }

    feed_map = {}

    for feed in feeds:
        feed_id = feed.get("id")

        if feed_id:
            feed_map[feed_id] = feed

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

    # Mely csatornák rendelkeznek megfelelő
    # magyar, országos feed-del?
    valid_channels = {}

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

        if not is_hungarian_feed(
            feed
        ):
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

        if is_local_area(feed):
            continue

        if local_name_check(
            channel,
            feed
        ):
            continue

        if not is_countrywide(
            feed
        ):
            continue

        old = valid_channels.get(
            channel_id
        )

        # Több országos feed esetén az is_main
        # legyen az elsődleges.
        if old is None:
            valid_channels[
                channel_id
            ] = feed

        elif feed.get(
            "is_main",
            False
        ):
            valid_channels[
                channel_id
            ] = feed

    print(
        "Megfelelő magyar országos csatornák:",
        len(valid_channels)
    )

    # Az index.m3u bejegyzéseit összepárosítjuk
    # az API-ban megtalált csatornákkal.
    result = []

    for entry in entries:

        info = entry["info"]
        url = entry["url"]

        if not url:
            continue

        channel_id = get_attr(
            info,
            "tvg-id"
        )

        if not channel_id:
            continue

        if channel_id not in valid_channels:
            continue

        channel = channel_map.get(
            channel_id
        )

        if not channel:
            continue

        feed = valid_channels[
            channel_id
        ]

        # Ha a playlistben van feed azonosító,
        # ellenőrizzük azt is.
        playlist_feed = get_attr(
            info,
            "tvg-feed"
        )

        if (
            playlist_feed
            and playlist_feed != feed.get("id")
        ):
            continue

        name = channel.get(
            "name",
            channel_id
        )

        logo = logo_map.get(
            channel_id,
            ""
        )

        result.append({
            "id": channel_id,
            "name": name,
            "logo": logo,
            "url": url,
        })

    # Egy csatorna csak egyszer szerepeljen.
    unique = {}

    for item in result:
        if item["id"] not in unique:
            unique[item["id"]] = item

    result = list(
        unique.values()
    )

    result.sort(
        key=lambda x:
        x["name"].lower()
    )

    output = [
        "#EXTM3U"
    ]

    for item in result:

        output.append(
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
        "magyar.m3u sikeresen elkészült."
    )


if __name__ == "__main__":
    main()
