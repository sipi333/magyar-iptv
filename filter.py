import json
import urllib.request
from pathlib import Path


# ============================================================
# BEÁLLÍTÁSOK
# ============================================================

API = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API}/channels.json"
FEEDS_URL = f"{API}/feeds.json"
STREAMS_URL = f"{API}/streams.json"
LOGOS_URL = f"{API}/logos.json"

OUTPUT = Path("magyar.m3u")

HUNGARY = "HU"
HUNGARIAN = "hun"

# Vallási kategória kizárása
EXCLUDED_CATEGORIES = {
    "religious",
}


# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def download_json(url):
    print(f"Letöltés: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "sipi333-magyar-iptv/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def quality_value(value):
    """
    Stream minőségből számot készít.

    Példák:
        1080p -> 1080
        720p  -> 720
        576i  -> 576
        480p  -> 480
        None  -> 0
        ""    -> 0
    """

    if not value:
        return 0

    text = str(value)

    digits = ""

    for character in text:
        if character.isdigit():
            digits += character

    if not digits:
        return 0

    try:
        return int(digits)
    except ValueError:
        return 0


def is_religious(channel):
    """
    Vallási csatornák kizárása.
    """

    categories = {
        clean_text(category).lower()
        for category in channel.get("categories", [])
    }

    return bool(
        categories.intersection(EXCLUDED_CATEGORIES)
    )


def is_national_hungarian_feed(feed, channel):
    """
    Csak magyar nyelvű, magyarországi, országos feed.

    c/HU = országos Magyarország
    r/   = régió
    s/   = megye / subdivision
    ct/  = város
    """

    # --------------------------------------------------------
    # Magyarországhoz tartozó csatorna
    # --------------------------------------------------------

    if clean_text(channel.get("country")).upper() != HUNGARY:
        return False

    # --------------------------------------------------------
    # Vallási csatorna kizárása
    # --------------------------------------------------------

    if is_religious(channel):
        return False

    # --------------------------------------------------------
    # Magyar nyelv
    # --------------------------------------------------------

    languages = {
        clean_text(language).lower()
        for language in feed.get("languages", [])
    }

    if HUNGARIAN not in languages:
        return False

    # --------------------------------------------------------
    # Sugárzási terület
    # --------------------------------------------------------

    areas = {
        clean_text(area).lower()
        for area in feed.get("broadcast_area", [])
    }

    # Csak országos Magyarország
    if "c/hu" not in areas:
        return False

    # Ha regionális / megyei / városi terület is szerepel,
    # a feedet kizárjuk.
    for area in areas:

        if area.startswith("r/"):
            return False

        if area.startswith("s/"):
            return False

        if area.startswith("ct/"):
            return False

    return True


def choose_logo(logos, channel_id, feed_id):
    """
    Megpróbálja kiválasztani a megfelelő csatornalogót.
    """

    # 1. Feedhez tartozó, használatban lévő logó
    for logo in logos:

        if (
            logo.get("channel") == channel_id
            and logo.get("feed") == feed_id
            and logo.get("in_use") is True
        ):
            return clean_text(logo.get("url"))

    # 2. Feedhez tartozó bármilyen logó
    for logo in logos:

        if (
            logo.get("channel") == channel_id
            and logo.get("feed") == feed_id
        ):
            return clean_text(logo.get("url"))

    # 3. Általános, használatban lévő csatornalogó
    for logo in logos:

        if (
            logo.get("channel") == channel_id
            and not logo.get("feed")
            and logo.get("in_use") is True
        ):
            return clean_text(logo.get("url"))

    # 4. Bármilyen általános csatornalogó
    for logo in logos:

        if (
            logo.get("channel") == channel_id
            and not logo.get("feed")
        ):
            return clean_text(logo.get("url"))

    return ""


def escape_m3u(value):
    """
    M3U attribútumokhoz biztonságosabb szöveg.
    """

    return clean_text(value).replace('"', "'")


# ============================================================
# FŐ PROGRAM
# ============================================================

def main():

    print("")
    print("==============================================")
    print(" Magyar IPTV playlist generátor")
    print("==============================================")
    print("")

    # --------------------------------------------------------
    # ADATOK LETÖLTÉSE
    # --------------------------------------------------------

    channels = download_json(CHANNELS_URL)
    feeds = download_json(FEEDS_URL)
    streams = download_json(STREAMS_URL)
    logos = download_json(LOGOS_URL)

    print("")
    print(f"Csatornák az API-ban: {len(channels)}")
    print(f"Feedek az API-ban:    {len(feeds)}")
    print(f"Streamek az API-ban:  {len(streams)}")
    print(f"Logók az API-ban:     {len(logos)}")
    print("")

    # --------------------------------------------------------
    # CSATORNÁK INDEXELÉSE
    # --------------------------------------------------------

    channels_by_id = {
        channel.get("id"): channel
        for channel in channels
        if channel.get("id")
    }

    # --------------------------------------------------------
    # VALLÁSI ÉS NEM KÍVÁNT FEED SZŰRÉSE
    # --------------------------------------------------------

    valid_feeds = []

    for feed in feeds:

        channel_id = feed.get("channel")

        if not channel_id:
            continue

        channel = channels_by_id.get(channel_id)

        if not channel:
            continue

        if not is_national_hungarian_feed(
            feed,
            channel
        ):
            continue

        valid_feeds.append(feed)

    print(
        "Magyar, országos, nem vallási feedek: "
        f"{len(valid_feeds)}"
    )

    # --------------------------------------------------------
    # ÉRVÉNYES FEED AZONOSÍTÓK
    # --------------------------------------------------------

    valid_feed_keys = {
        (
            feed.get("channel"),
            feed.get("id")
        )
        for feed in valid_feeds
    }

    # --------------------------------------------------------
    # STREAMEK CSOPORTOSÍTÁSA
    # --------------------------------------------------------

    streams_by_feed = {}

    for stream in streams:

        channel_id = stream.get("channel")
        feed_id = stream.get("feed")
        url = stream.get("url")

        if not url:
            continue

        key = (
            channel_id,
            feed_id
        )

        if key not in valid_feed_keys:
            continue

        if key not in streams_by_feed:
            streams_by_feed[key] = []

        streams_by_feed[key].append(stream)

    print(
        "Érvényes feedekhez tartozó stream-csoportok: "
        f"{len(streams_by_feed)}"
    )

    # --------------------------------------------------------
    # PLAYLIST BEJEGYZÉSEK
    # --------------------------------------------------------

    entries = []

    for feed in valid_feeds:

        channel_id = feed.get("channel")
        feed_id = feed.get("id")

        channel = channels_by_id.get(channel_id)

        if not channel:
            continue

        key = (
            channel_id,
            feed_id
        )

        available_streams = streams_by_feed.get(
            key,
            []
        )

        if not available_streams:
            continue

        # ----------------------------------------------------
        # STREAM KIVÁLASZTÁSA
        # ----------------------------------------------------

        # Először azokat részesítjük előnyben,
        # amelyeknél nincs problémajelző label.
        #
        # Második szempont:
        # magasabb felbontás.

        available_streams.sort(
            key=lambda stream: (
                bool(stream.get("label")),
                -quality_value(
                    stream.get("quality")
                )
            )
        )

        stream = available_streams[0]

        # ----------------------------------------------------
        # NÉV
        # ----------------------------------------------------

        name = clean_text(
            channel.get("name")
        )

        if not name:
            name = clean_text(
                feed.get("name")
            )

        if not name:
            name = channel_id

        # ----------------------------------------------------
        # LOGÓ
        # ----------------------------------------------------

        logo = choose_logo(
            logos,
            channel_id,
            feed_id
        )

        # ----------------------------------------------------
        # BEJEGYZÉS
        # ----------------------------------------------------

        entries.append({
            "channel_id": channel_id,
            "feed_id": feed_id,
            "name": name,
            "logo": logo,
            "url": clean_text(
                stream.get("url")
            ),
            "referrer": clean_text(
                stream.get("referrer")
            ),
            "user_agent": clean_text(
                stream.get("user_agent")
            ),
            "quality": clean_text(
                stream.get("quality")
            ),
        })

    # --------------------------------------------------------
    # DUPLIKÁCIÓK KISZŰRÉSE
    # --------------------------------------------------------

    unique_entries = {}

    for entry in entries:

        channel_id = entry["channel_id"]

        if channel_id not in unique_entries:
            unique_entries[channel_id] = entry
            continue

        # Ha már van bejegyzés, csak akkor cseréljük,
        # ha az új stream jobb minőségű.

        old_entry = unique_entries[channel_id]

        old_quality = quality_value(
            old_entry.get("quality")
        )

        new_quality = quality_value(
            entry.get("quality")
        )

        if new_quality > old_quality:
            unique_entries[channel_id] = entry

    entries = list(
        unique_entries.values()
    )

    # --------------------------------------------------------
    # ABC SORREND
    # --------------------------------------------------------

    entries.sort(
        key=lambda entry:
        entry["name"].casefold()
    )

    print(
        "Végleges csatornák száma: "
        f"{len(entries)}"
    )

    # --------------------------------------------------------
    # M3U LÉTREHOZÁSA
    # --------------------------------------------------------

    lines = []

    lines.append(
        "#EXTM3U"
    )

    lines.append(
        "# Magyar nyelvű országos TV csatornák"
    )

    lines.append(
        "# Vallási, regionális, megyei és városi csatornák kizárva"
    )

    lines.append("")

    for entry in entries:

        name = escape_m3u(
            entry["name"]
        )

        channel_id = escape_m3u(
            entry["channel_id"]
        )

        logo = escape_m3u(
            entry["logo"]
        )

        lines.append(
            '#EXTINF:-1 '
            f'tvg-id="{channel_id}" '
            f'tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            'group-title="🇭🇺 Magyarország",'
            f'{name}'
        )

        # Referer
        if entry.get("referrer"):

            referrer = escape_m3u(
                entry["referrer"]
            )

            lines.append(
                '#EXTVLCOPT:http-referrer='
                f'{referrer}'
            )

        # User-Agent
        if entry.get("user_agent"):

            user_agent = escape_m3u(
                entry["user_agent"]
            )

            lines.append(
                '#EXTVLCOPT:http-user-agent='
                f'{user_agent}'
            )

        # Stream URL
        lines.append(
            entry["url"]
        )

        lines.append("")

    # --------------------------------------------------------
    # FÁJL MENTÉSE
    # --------------------------------------------------------

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print("")
    print("==============================================")
    print(" KÉSZ")
    print("==============================================")
    print(
        f"Playlist: {OUTPUT}"
    )
    print(
        f"Csatornák: {len(entries)}"
    )
    print("")


if __name__ == "__main__":
    main()
