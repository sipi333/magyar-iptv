import json
import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/index.m3u"
API = "https://iptv-org.github.io/api"
OUTPUT = Path("magyar.m3u")

EXCLUDE_IDS = {
    "BTV.hu",
}

RELIGIOUS = {
    "religious",
}

RADIO = {
    "radio",
}

LOCAL_WORDS = (
    "városi tv", "varosi tv",
    "városi televízió", "varosi televizio",
    "helyi tv", "helyi televízió",
    "helyi televizio",
    "regionális tv", "regionalis tv",
    "régiós tv", "regios tv",
    "térségi tv", "tersegi tv",
    "megyei tv", "megye tv",
    "kerületi tv", "keruleti tv",
    "önkormányzati tv", "onkormanyzati tv",
    "közösségi tv", "kozossegi tv",
    "local tv", "localtv",
    "city tv", "citytv",
)

RELIGIOUS_WORDS = (
    "ewtn",
    "apostol tv",
    "apostol",
    "bonum",
    "katolikus",
    "catholic",
    "református",
    "reformatus",
    "evangélikus",
    "evangelikus",
    "keresztény",
    "kereszteny",
    "christian",
    "gospel",
    "church",
    "biblia",
    "bible",
)

RADIO_WORDS = (
    "rádió",
    "radio",
)


def download(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request,
        timeout=180
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def get_json(name):
    return json.loads(
        download(API + "/" + name)
    )


def attr(line, name):
    match = re.search(
        r'(?:^|\s)' + re.escape(name) + r'="([^"]*)"',
        line
    )
    return match.group(1) if match else ""


def parse_m3u(text):
    result = []
    current = None

    for raw in text.splitlines():
        line = raw.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current = {
                "info": line,
                "url": None,
            }
            continue

        if current is None:
            continue

        if line.startswith("#"):
            continue

        current["url"] = line
        result.append(current)
        current = None

    return result


def norm(value):
    return str(value or "").lower().strip()


def channel_text(channel, feed):
    values = [
        channel.get("name", ""),
        feed.get("name", ""),
    ]

    values.extend(
        channel.get("alt_names", [])
    )

    values.extend(
        feed.get("alt_names", [])
    )

    return norm(" ".join(map(str, values)))


def has_any(text, words):
    return any(
        word in text
        for word in words
    )


def is_local(feed):
    for area in feed.get(
        "broadcast_area",
        []
    ):
        area = str(area)

        if (
            area.startswith("r/")
            or area.startswith("s/")
            or area.startswith("ct/")
        ):
            return True

    return False


def has_hungarian(feed):
    return "hun" in feed.get(
        "languages",
        []
    )


def is_hungarian_channel(channel):
    return channel.get(
        "country"
    ) == "HU"


def main():

    print("index.m3u letöltése...")

    entries = parse_m3u(
        download(SOURCE)
    )

    print(
        "M3U bejegyzések:",
        len(entries)
    )

    print("API adatok letöltése...")

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
        c["id"]: c
        for c in channels
        if c.get("id")
    }

    feeds_by_channel = {}

    for feed in feeds:
        cid = feed.get("channel")

        if cid:
            feeds_by_channel.setdefault(
                cid,
                []
            ).append(feed)

    logo_map = {}

    for logo in logos:
        cid = logo.get("channel")

        if not cid:
            continue

        if (
            logo.get("in_use")
            or cid not in logo_map
        ):
            logo_map[cid] = logo.get(
                "url",
                ""
            )

    # -------------------------------------------------
    # Megfelelő magyar csatornák meghatározása.
    #
    # FONTOS:
    # Nem követeljük meg minden esetben a c/HU-t.
    # A magyar nyelv + HU ország + helyi terület
    # kizárása együtt dönt.
    # -------------------------------------------------

    valid = {}

    for cid, channel in channel_map.items():

        if cid in EXCLUDE_IDS:
            continue

        if not is_hungarian_channel(
            channel
        ):
            continue

        categories = {
            norm(x)
            for x in channel.get(
                "categories",
                []
            )
        }

        if categories & RELIGIOUS:
            continue

        if categories & RADIO:
            continue

        candidates = []

        for feed in feeds_by_channel.get(
            cid,
            []
        ):

            if not has_hungarian(
                feed
            ):
                continue

            text = channel_text(
                channel,
                feed
            )

            if has_any(
                text,
                LOCAL_WORDS
            ):
                continue

            if has_any(
                text,
                RELIGIOUS_WORDS
            ):
                continue

            if has_any(
                text,
                RADIO_WORDS
            ):
                continue

            # Városi/régiós feed kizárása.
            if is_local(feed):
                continue

            candidates.append(feed)

        if not candidates:
            continue

        # Elsőként az is_main feedet választjuk.
        candidates.sort(
            key=lambda f: (
                not bool(
                    f.get(
                        "is_main",
                        False
                    )
                ),
                norm(
                    f.get(
                        "name",
                        ""
                    )
                )
            )
        )

        valid[cid] = candidates[0]

    print(
        "Magyar, nem helyi csatornák:",
        len(valid)
    )

    # -------------------------------------------------
    # Stream kiválasztása
    # -------------------------------------------------

    best = {}

    for stream in streams:

        cid = stream.get(
            "channel"
        )

        if cid not in valid:
            continue

        url = stream.get(
            "url"
        )

        if not url:
            continue

        feed_id = stream.get(
            "feed"
        )

        selected_feed = valid[cid]

        # Ha van feed azonosító, annak egyeznie kell.
        if (
            feed_id
            and feed_id != selected_feed.get("id")
        ):
            continue

        quality = str(
            stream.get(
                "quality"
            ) or ""
        )

        numbers = re.findall(
            r"\d+",
            quality
        )

        score = (
            int(numbers[0])
            if numbers
            else 0
        )

        old = best.get(cid)

        if (
            old is None
            or score > old[0]
        ):
            best[cid] = (
                score,
                stream
            )

    # -------------------------------------------------
    # M3U létrehozása
    # -------------------------------------------------

    result = []

    for cid, data in best.items():

        channel = channel_map.get(
            cid
        )

        if not channel:
            continue

        stream = data[1]

        result.append({
            "id": cid,
            "name": channel.get(
                "name",
                cid
            ),
            "logo": logo_map.get(
                cid,
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
            ),
        })

    result.sort(
        key=lambda x:
        norm(x["name"])
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
