import json
import re
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


# ============================================================
# KIZÁRANDÓ KATEGÓRIÁK
# ============================================================

EXCLUDED_CATEGORIES = {
    "religious",
}


# ============================================================
# HELYI / VÁROSI / REGIONÁLIS NÉVJELZÉSEK
#
# Nem városneveket sorolunk fel, hanem azokat a kifejezéseket
# keressük, amelyekből általában felismerhető egy helyi TV.
# ============================================================

LOCAL_NAME_PATTERNS = [
    r"\bv[aá]rosi\s+tv\b",
    r"\bv[aá]rosi\s+telev[ií]zi[oó]\b",
    r"\bv[aá]rosi\s+telev[ií]zi[oó]ja\b",

    r"\bregion[aá]lis\s+tv\b",
    r"\bregion[aá]lis\s+telev[ií]zi[oó]\b",

    r"\br[eé]gi[oó]s\s+tv\b",
    r"\br[eé]gi[oó]s\s+telev[ií]zi[oó]\b",

    r"\bt[eé]rs[eé]gi\s+tv\b",
    r"\bt[eé]rs[eé]gi\s+telev[ií]zi[oó]\b",

    r"\bhelyi\s+tv\b",
    r"\bhelyi\s+telev[ií]zi[oó]\b",

    r"\bker[uü]leti\s+tv\b",
    r"\bker[uü]leti\s+telev[ií]zi[oó]\b",

    r"\b[oö]nkorm[aá]nyzati\s+tv\b",
    r"\b[oö]nkorm[aá]nyzati\s+telev[ií]zi[oó]\b",

    r"\bcommunity\s+tv\b",
    r"\blocal\s+tv\b",
]


# Néhány tipikus helyi csatorna-formátum.
# Ezek nem városlista helyett szolgálnak, hanem biztonsági
# szűrőként az olyan nevekre, amelyek egyértelműen helyi adók.

LOCAL_SUFFIX_PATTERNS = [
    r"\bTV\s+\w+$",
    r"\bVTV\b",
]


# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def download_json(url):
    print(f"Letöltés: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "sipi333-magyar-iptv/2.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        return json.load(response)


def text(value):
    if value is None:
        return ""

    return str(value).strip()


def normalize(value):
    return text(value).casefold()


def quality_value(value):
    """
    1080p -> 1080
    720p  -> 720
    576i  -> 576
    None  -> 0
    """

    if not value:
        return 0

    digits = "".join(
        character
        for character in str(value)
        if character.isdigit()
    )

    if not digits:
        return 0

    try:
        return int(digits)
    except ValueError:
        return 0


# ============================================================
# VALLÁSI SZŰRÉS
# ============================================================

def is_religious(channel):
    categories = {
        normalize(category)
        for category in channel.get(
            "categories",
            []
        )
    }

    return bool(
        categories.intersection(
            EXCLUDED_CATEGORIES
        )
    )


# ============================================================
# HELYI / VÁROSI NÉVSZŰRÉS
# ============================================================

def looks_like_local_channel(channel, feed):
    """
    Biztonsági szűrő az egyértelműen helyi/városi/
    regionális csatornanevekre.

    Nem konkrét városlistát használunk.
    """

    names = []

    names.append(
        text(channel.get("name"))
    )

    names.extend(
        text(x)
        for x in channel.get(
            "alt_names",
            []
        )
    )

    names.append(
        text(feed.get("name"))
    )

    names.extend(
        text(x)
        for x in feed.get(
            "alt_names",
            []
        )
    )

    for original_name in names:

        if not original_name:
            continue

        name = normalize(original_name)

        # Egyértelmű helyi megnevezések
        for pattern in LOCAL_NAME_PATTERNS:

            if re.search(
                pattern,
                name,
                flags=re.IGNORECASE
            ):
                return True

    return False


# ============================================================
# FEED SZŰRÉSE
# ============================================================

def is_valid_feed(feed, channel):

    # --------------------------------------------------------
    # Magyarország
    # --------------------------------------------------------

    if normalize(
        channel.get("country")
    ).upper() != HUNGARY:

        return False

    # --------------------------------------------------------
    # Vallási csatorna
    # --------------------------------------------------------

    if is_religious(channel):
        return False

    # --------------------------------------------------------
    # Magyar nyelv
    # --------------------------------------------------------

    languages = {
        normalize(language)
        for language in feed.get(
            "languages",
            []
        )
    }

    if HUNGARIAN not in languages:
        return False

    # --------------------------------------------------------
    # Broadcast area
    # --------------------------------------------------------

    areas = {
        normalize(area)
        for area in feed.get(
            "broadcast_area",
            []
        )
    }

    # Magyarország országos feedje
    if "c/hu" not in areas:
        return False

    # Ha ugyanaz a feed regionális,
    # megyei vagy városi területet is megjelöl,
    # kizárjuk.

    for area in areas:

        if area.startswith("r/"):
            return False

        if area.startswith("s/"):
            return False

        if area.startswith("ct/"):
            return False

    # --------------------------------------------------------
    # Helyi/városi név alapján extra védelem
    # --------------------------------------------------------

    if looks_like_local_channel(
        channel,
        feed
    ):
        return False

    return True


# ============================================================
# LOGÓ
# ============================================================

def choose_logo(
    logos,
    channel_id,
    feed_id
):

    # Feedhez tartozó használatban lévő logó
    for logo in logos:

        if (
            logo.get("channel")
            == channel_id
            and logo.get("feed")
            == feed_id
            and logo.get("in_use")
            is True
        ):
            return text(
                logo.get("url")
            )

    # Feedhez tartozó bármilyen logó
    for logo in logos:

        if (
            logo.get("channel")
            == channel_id
            and logo.get("feed")
            == feed_id
        ):
            return text(
                logo.get("url")
            )

    # Általános használatban lévő logó
    for logo in logos:

        if (
            logo.get("channel")
            == channel_id
            and not logo.get("feed")
            and logo.get("in_use")
            is True
        ):
            return text(
                logo.get("url")
            )

    # Általános logó
    for logo in logos:

        if (
            logo.get("channel")
            == channel_id
            and not logo.get("feed")
        ):
            return text(
                logo.get("url")
            )

    return ""


# ============================================================
# M3U ESCAPE
# ============================================================

def escape_m3u(value):

    return text(value).replace(
        '"',
        "'"
    )


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print("")
    print("==============================================")
    print(" Magyar IPTV szűrő")
    print("==============================================")
    print("")

    # --------------------------------------------------------
    # API ADATOK
    # --------------------------------------------------------

    channels = download_json(
        CHANNELS_URL
    )

    feeds = download_json(
        FEEDS_URL
    )

    streams = download_json(
        STREAMS_URL
    )

    logos = download_json(
        LOGOS_URL
    )

    print("")
    print(
        f"Csatornák: {len(channels)}"
    )
    print(
        f"Feedek:    {len(feeds)}"
    )
    print(
        f"Streamek:  {len(streams)}"
    )
    print(
        f"Logók:     {len(logos)}"
    )
    print("")

    # --------------------------------------------------------
    # CSATORNA INDEX
    # --------------------------------------------------------

    channels_by_id = {
        channel["id"]: channel
        for channel in channels
        if channel.get("id")
    }

    # --------------------------------------------------------
    # VALID FEED
    # --------------------------------------------------------

    valid_feeds = []

    rejected_religious = 0
    rejected_local = 0
    rejected_area = 0
    rejected_language = 0

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

        # ----------------------------------------------------
        # Magyarország
        # ----------------------------------------------------

        if normalize(
            channel.get("country")
        ).upper() != HUNGARY:

            continue

        # ----------------------------------------------------
        # Vallási
        # ----------------------------------------------------

        if is_religious(channel):

            rejected_religious += 1
            continue

        # ----------------------------------------------------
        # Magyar nyelv
        # ----------------------------------------------------

        languages = {
            normalize(language)
            for language in feed.get(
                "languages",
                []
            )
        }

        if HUNGARIAN not in languages:

            rejected_language += 1
            continue

        # ----------------------------------------------------
        # Broadcast area
        # ----------------------------------------------------

        areas = {
            normalize(area)
            for area in feed.get(
                "broadcast_area",
                []
            )
        }

        if "c/hu" not in areas:

            rejected_area += 1
            continue

        is_local_area = False

        for area in areas:

            if area.startswith("r/"):
                is_local_area = True

            elif area.startswith("s/"):
                is_local_area = True

            elif area.startswith("ct/"):
                is_local_area = True

        if is_local_area:

            rejected_area += 1
            continue

        # ----------------------------------------------------
        # Név alapú helyi szűrés
        # ----------------------------------------------------

        if looks_like_local_channel(
            channel,
            feed
        ):

            rejected_local += 1
            continue

        valid_feeds.append(
            feed
        )

    print(
        "----------------------------------------------"
    )

    print(
        "Kizárt vallási feedek: "
        f"{rejected_religious}"
    )

    print(
        "Kizárt területi feedek: "
        f"{rejected_area}"
    )

    print(
        "Kizárt helyi név alapján: "
        f"{rejected_local}"
    )

    print(
        "Kizárt nem magyar nyelv: "
        f"{rejected_language}"
    )

    print(
        "----------------------------------------------"
    )

    print(
        "Érvényes feedek: "
        f"{len(valid_feeds)}"
    )

    # --------------------------------------------------------
    # ÉRVÉNYES FEED KULCSOK
    # --------------------------------------------------------

    valid_keys = {
        (
            feed.get("channel"),
            feed.get("id")
        )
        for feed in valid_feeds
    }

    # --------------------------------------------------------
    # STREAMEK
    # --------------------------------------------------------

    streams_by_feed = {}

    for stream in streams:

        channel_id = stream.get(
            "channel"
        )

        feed_id = stream.get(
            "feed"
        )

        url = text(
            stream.get("url")
        )

        if not url:
            continue

        key = (
            channel_id,
            feed_id
        )

        if key not in valid_keys:
            continue

        streams_by_feed.setdefault(
            key,
            []
        ).append(
            stream
        )

    # --------------------------------------------------------
    # PLAYLIST BEJEGYZÉSEK
    # --------------------------------------------------------

    entries = []

    for feed in valid_feeds:

        channel_id = feed.get(
            "channel"
        )

        feed_id = feed.get(
            "id"
        )

        channel = channels_by_id.get(
            channel_id
        )

        if not channel:
            continue

        key = (
            channel_id,
            feed_id
        )

        available = streams_by_feed.get(
            key,
            []
        )

        if not available:
            continue

        # ----------------------------------------------------
        # STREAM KIVÁLASZTÁS
        # ----------------------------------------------------

        def stream_sort_key(stream):

            label = text(
                stream.get("label")
            )

            # A geo-blocked / problémás stream
            # hátrébb kerül.
            has_label = bool(
                label
            )

            quality = quality_value(
                stream.get("quality")
            )

            return (
                has_label,
                -quality
            )

        available.sort(
            key=stream_sort_key
        )

        stream = available[0]

        # ----------------------------------------------------
        # NÉV
        # ----------------------------------------------------

        name = text(
            channel.get("name")
        )

        if not name:

            name = text(
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

        entries.append({
            "channel_id": channel_id,
            "feed_id": feed_id,
            "name": name,
            "logo": logo,
            "url": text(
                stream.get("url")
            ),
            "referrer": text(
                stream.get("referrer")
            ),
            "user_agent": text(
                stream.get("user_agent")
            ),
            "quality": text(
                stream.get("quality")
            ),
        })

    # --------------------------------------------------------
    # DUPLIKÁCIÓ
    # --------------------------------------------------------

    unique = {}

    for entry in entries:

        channel_id = entry[
            "channel_id"
        ]

        if channel_id not in unique:

            unique[channel_id] = entry

            continue

        old = unique[
            channel_id
        ]

        old_quality = quality_value(
            old.get("quality")
        )

        new_quality = quality_value(
            entry.get("quality")
        )

        if new_quality > old_quality:

            unique[
                channel_id
            ] = entry

    entries = list(
        unique.values()
    )

    # --------------------------------------------------------
    # ABC SORREND
    # --------------------------------------------------------

    entries.sort(
        key=lambda x:
        x["name"].casefold()
    )

    print("")
    print(
        "=============================================="
    )

    print(
        "VÉGLEGES CSATORNÁK: "
        f"{len(entries)}"
    )

    print(
        "=============================================="
    )

    # --------------------------------------------------------
    # M3U
    # --------------------------------------------------------

    lines = [
        "#EXTM3U",
        "#",
        "# Magyar nyelvű országos TV csatornák",
        "# Vallási, regionális, megyei és városi TV-k kizárva",
        "# Automatikusan generálva az iptv-org API alapján",
        "#",
        ""
    ]

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

        if entry.get(
            "referrer"
        ):

            lines.append(
                "#EXTVLCOPT:http-referrer="
                + escape_m3u(
                    entry["referrer"]
                )
            )

        if entry.get(
            "user_agent"
        ):

            lines.append(
                "#EXTVLCOPT:http-user-agent="
                + escape_m3u(
                    entry["user_agent"]
                )
            )

        lines.append(
            entry["url"]
        )

        lines.append("")

    # --------------------------------------------------------
    # MENTÉS
    # --------------------------------------------------------

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print("")
    print(
        "Playlist elkészült:"
    )

    print(
        OUTPUT
    )

    print("")
    print(
        "Automatikus frissítésre kész."
    )


if __name__ == "__main__":
    main()
