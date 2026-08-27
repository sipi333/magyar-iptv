import json
import urllib.request
from pathlib import Path

API = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API}/channels.json"
FEEDS_URL = f"{API}/feeds.json"
STREAMS_URL = f"{API}/streams.json"
LOGOS_URL = f"{API}/logos.json"

OUTPUT = Path("magyar.m3u")

HUNGARY = "HU"
HUNGARIAN = "hun"

# Ezeket a kategóriákat kizárjuk.
EXCLUDED_CATEGORIES = {
    "religious",
}

# Nem országos területek:
# r/  = régió
# s/  = megye / subdivision
# ct/ = város
EXCLUDED_AREA_PREFIXES = (
    "r/",
    "s/",
    "ct/",
)


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "sipi333-magyar-iptv/1.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def is_hungarian_national_feed(feed, channel):
    # Csak magyarországi csatorna
    if channel.get("country") != HUNGARY:
        return False

    # Magyar nyelvnek szerepelnie kell
    languages = {
        str(x).lower()
        for x in feed.get("languages", [])
    }

    if HUNGARIAN not in languages:
        return False

    # Országos magyar feed szükséges
    areas = {
        str(x).lower()
        for x in feed.get("broadcast_area", [])
    }

    if "c/hu" not in areas:
        return False

    # Régiós, megyei vagy városi feed kizárása
    for area in areas:
        if area.startswith(EXCLUDED_AREA_PREFIXES):
            return False

    # Vallási csatorna kizárása
    categories = {
        str(x).lower()
        for x in channel.get("categories", [])
    }

    if categories.intersection(EXCLUDED_CATEGORIES):
        return False

    return True


def choose_logo(logos, channel_id, feed_id):
    # Először feedhez tartozó logót keresünk
    for logo in logos:
        if (
            logo.get("channel") == channel_id
            and logo.get("feed") == feed_id
            and logo.get("in_use") is True
        ):
            return logo.get("url")

    # Második lehetőség: feedhez tartozó bármilyen logó
    for logo in logos:
        if (
            logo.get("channel") == channel_id
            and logo.get("feed") == feed_id
        ):
            return logo.get("url")

    # Végül általános csatornalogó
    for logo in logos:
        if (
            logo.get("channel") == channel_id
            and not logo.get("feed")
            and logo.get("in_use") is True
        ):
            return logo.get("url")

    for logo in logos:
        if (
            logo.get("channel") == channel_id
            and not logo.get("feed")
        ):
            return logo.get("url")

    return ""


def main():
    print("iptv-org adatok letöltése...")

    channels = get_json(CHANNELS_URL)
    feeds = get_json(FEEDS_URL)
    streams = get_json(STREAMS_URL)
    logos = get_json(LOGOS_URL)

    channels_by_id = {
        channel["id"]: channel
        for channel in channels
    }

    logos_by_channel_feed = {}

    for logo in logos:
        key = (
            logo.get("channel"),
            logo.get("feed")
        )

        if key not in logos_by_channel_feed:
            logos_by_channel_feed[key] = logo

    # Érvényes feedek
    valid_feeds = []

    for feed in feeds:
        channel_id = feed.get("channel")

        if not channel_id:
            continue

        channel = channels_by_id.get(channel_id)

        if not channel:
            continue

        if not is_hungarian_national_feed(feed, channel):
            continue

        valid_feeds.append(feed)

    print(
        f"Magyar, országos, nem vallási feedek: "
        f"{len(valid_feeds)}"
    )

    valid_feed_keys = {
        (
            feed.get("channel"),
            feed.get("id")
        )
        for feed in valid_feeds
    }

    # Streamek hozzárendelése
    streams_by_feed = {}

    for stream in streams:
        key = (
            stream.get("channel"),
            stream.get("feed")
        )

        if key not in valid_feed_keys:
            continue

        url = stream.get("url")

        if not url:
            continue

        if key not in streams_by_feed:
            streams_by_feed[key] = []

        streams_by_feed[key].append(stream)

    entries = []

    for feed in valid_feeds:
        channel_id = feed.get("channel")
        feed_id = feed.get("id")

        channel = channels_by_id.get(channel_id)

        if not channel:
            continue

        key = (channel_id, feed_id)

        available = streams_by_feed.get(key, [])

        if not available:
            continue

        # Előnyben a minőségi stream,
        # de olyan streamet válasszunk,
        # amely nincs hibaként megjelölve.
        available.sort(
            key=lambda x: (
                bool(x.get("label")),
                -(int(
                    str(x.get("quality", "0"))
                    .replace("p", "")
                    .replace("i", "")
                ) or 0)
            )
        )

        stream = available[0]

        logo = choose_logo(
            logos,
            channel_id,
            feed_id
        )

        entries.append({
            "id": channel_id,
            "name": channel.get("name", channel_id),
            "logo": logo,
            "url": stream.get("url"),
            "referrer": stream.get("referrer"),
            "user_agent": stream.get("user_agent"),
        })

    # Egy csatorna csak egyszer szerepeljen.
    unique = {}

    for entry in entries:
        channel_id = entry["id"]

        if channel_id not in unique:
            unique[channel_id] = entry

    entries = list(unique.values())

    # ABC sorrend
    entries.sort(
        key=lambda x: x["name"].casefold()
    )

    print(
        f"Végleges csatornák száma: {len(entries)}"
    )

    lines = [
        "#EXTM3U",
        "# Magyar nyelvű országos csatornák",
        "# Vallási, regionális, megyei és városi csatornák kizárva",
        "",
    ]

    for entry in entries:
        name = entry["name"].replace('"', "'")
        logo = entry["logo"].replace('"', "'")
        channel_id = entry["id"].replace('"', "'")

        lines.append(
            f'#EXTINF:-1 '
            f'tvg-id="{channel_id}" '
            f'tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            f'group-title="🇭🇺 Magyarország",{name}'
        )

        if entry.get("referrer"):
            referrer = entry["referrer"].replace('"', "'")
            lines.append(
                f"#EXTVLCOPT:http-referrer={referrer}"
            )

        if entry.get("user_agent"):
            user_agent = entry["user_agent"].replace('"', "'")
            lines.append(
                f"#EXTVLCOPT:http-user-agent={user_agent}"
            )

        lines.append(entry["url"])
        lines.append("")

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print("magyar.m3u elkészült.")


if __name__ == "__main__":
    main()
