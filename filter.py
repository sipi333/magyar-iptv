import json
import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/index.m3u"
API = "https://iptv-org.github.io/api"
OUTPUT = Path("magyar.m3u")

# Ritka, problémás azonosítók, amelyeket külön kizárunk.
EXCLUDE_IDS = {
    "BTV.hu",
}

# Kizárt csatornakategóriák.
EXCLUDE_CATEGORIES = {
    "radio",
    "religious",
}

# Általános helyi/regionális jelölések.
LOCAL_WORDS = (
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
    "megye tv",
    "kerületi tv",
    "keruleti tv",
    "önkormányzati tv",
    "onkormanyzati tv",
    "city tv",
    "citytv",
    "local tv",
    "localtv",
)

RELIGIOUS_WORDS = (
    "ewtn",
    "apostol tv",
    "apostol",
    "bonum",
    "bizonyság",
    "bizonysag",
    "biblia",
    "bible",
    "christian",
    "christ",
    "gospel",
    "church",
    "katolikus",
    "catholic",
    "református",
    "reformatus",
    "evangélikus",
    "evangelikus",
    "keresztény",
    "kereszteny",
)

RADIO_WORDS = (
    "radio",
    "rádió",
    "radio.",
    "rádió.",
)


def normalize(text):
    text = str(text or "").lower()
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def download(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=180
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def get_json(filename):
    return json.loads(
        download(API + "/" + filename)
    )


def parse_m3u(text):
    result = []
    current = None

    for raw in text.splitlines():
        line = raw.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current = {
                "extinf": line,
                "extra": [],
                "url": None,
            }
            continue

        if current is None:
            continue

        if line.startswith("#"):
            current["extra"].append(line)
            continue

        current["url"] = line
        result.append(current)
        current = None

    return result


def attr(line, name):
    pattern = (
        r'(?:^|\s)'
        + re.escape(name)
        + r'="([^"]*)"'
    )

    match = re.search(
        pattern,
        line
    )

    if match:
        return match.group(1)

    return ""


def all_names(channel, feed=None):
    values = []

    values.append(
        channel.get("name", "")
    )

    values.extend(
        channel.get("alt_names", [])
    )

    if feed:
        values.append(
            feed.get("name", "")
        )

        values.extend(
            feed.get("alt_names", [])
        )

    return normalize(
        " ".join(
            str(x)
            for x in values
            if x
        )
    )


def has_words(text, words):
    return any(
        word in text
        for word in words
    )


def is_local_feed(feed):
    areas = feed.get(
        "broadcast_area",
        []
    )

    for area in areas:
        area = str(area)

        if (
            area.startswith("r/")
            or area.startswith("s/")
            or area.startswith("ct/")
        ):
            return True

    return False


def is_national_feed(feed):
    areas = feed.get(
        "broadcast_area",
        []
    )

    return "c/HU" in areas


def main():
    print("IPTV-org index.m3u letöltése...")

    playlist = download(
        SOURCE
    )

    entries = parse_m3u(
        playlist
    )

    print(
        "Index bejegyzések:",
        len(entries)
    )

    print("IPTV-org API letöltése...")

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

    # Csatorna -> feedek
    feeds_by_channel = {}

    for feed in feeds:
        channel_id = feed.get(
            "channel"
        )

        if not channel_id:
            continue

        feeds_by_channel.setdefault(
            channel_id,
            []
        ).append(feed)

    # Csatorna -> megfelelő országos feed
    valid_channels = {}

    for channel_id, channel in channel_map.items():

        if channel.get(
            "country"
        ) != "HU":
            continue

        if channel_id in EXCLUDE_IDS:
            continue

        categories = {
            normalize(x)
            for x in channel.get(
                "categories",
                []
            )
        }

        if categories.intersection(
            EXCLUDE_CATEGORIES
        ):
            continue

        candidates = []

        for feed in feeds_by_channel.get(
            channel_id,
            []
        ):

            languages = {
                normalize(x)
                for x in feed.get(
                    "languages",
                    []
                )
            }

            if "hun" not in languages:
                continue

            if is_local_feed(feed):
                continue

            if not is_national_feed(feed):
                continue

            names = all_names(
                channel,
                feed
            )

            if has_words(
                names,
                LOCAL_WORDS
            ):
                continue

            if has_words(
                names,
                RELIGIOUS_WORDS
            ):
                continue

            if has_words(
                names,
                RADIO_WORDS
            ):
                continue

            candidates.append(feed)

        if not candidates:
            continue

        # Az is_main feed legyen az elsődleges.
        candidates.sort(
            key=lambda feed: (
                not bool(
                    feed.get(
                        "is_main",
                        False
                    )
                ),
                normalize(
                    feed.get(
                        "name",
                        ""
                    )
                ),
            )
        )

        valid_channels[
            channel_id
        ] = candidates[0]

    print(
        "Megfelelő országos magyar csatornák:",
        len(valid_channels)
    )

    # Logo választás
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

    # Index M3U -> csatornaazonosító alapján.
    result = []
    seen = set()

    for entry in entries:

        info = entry["extinf"]
        url = entry["url"]

        if not url:
            continue

        channel_id = attr(
            info,
            "tvg-id"
        )

        if not channel_id:
            continue

        if channel_id in seen:
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

        # Biztonsági ellenőrzés.
        if not is_national_feed(feed):
            continue

        if is_local_feed(feed):
            continue

        name_text = all_names(
            channel,
            feed
        )

        if has_words(
            name_text,
            LOCAL_WORDS
        ):
            continue

        if has_words(
            name_text,
            RELIGIOUS_WORDS
        ):
            continue

        if has_words(
            name_text,
            RADIO_WORDS
        ):
            continue

        seen.add(
            channel_id
        )

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
            "url": url,
        })

    result.sort(
        key=lambda item:
        normalize(item["name"])
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
