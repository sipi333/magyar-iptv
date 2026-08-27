import json
import urllib.request
from pathlib import Path

API = "https://iptv-org.github.io/api"
OUTPUT = Path("magyar.m3u")


def get_data(file):
    req = urllib.request.Request(
        API + "/" + file,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def quality(value):
    text = str(value or "")
    digits = "".join(c for c in text if c.isdigit())
    return int(digits or 0)


def main():
    print("IPTV-org API letöltése...")

    channels = get_data("channels.json")
    feeds = get_data("feeds.json")
    streams = get_data("streams.json")
    logos = get_data("logos.json")

    channel_map = {
        x["id"]: x
        for x in channels
        if x.get("id")
    }

    logo_map = {}

    for logo in logos:
        cid = logo.get("channel")

        if not cid:
            continue

        if logo.get("in_use") or cid not in logo_map:
            logo_map[cid] = logo.get("url", "")

    valid_feeds = {}

    for feed in feeds:
        cid = feed.get("channel")

        if not cid:
            continue

        channel = channel_map.get(cid)

        if not channel:
            continue

        if channel.get("country") != "HU":
            continue

        languages = set(
            feed.get("languages", [])
        )

        if "hun" not in languages:
            continue

        categories = set(
            channel.get("categories", [])
        )

        if "religious" in categories:
            continue

        area = feed.get(
            "broadcast_area",
            []
        )

        # Csak Magyarország egészére sugárzó feed.
        # Regionális, megyei és városi feed kizárva.
        if "c/HU" not in area:
            continue

        # A fő feedet részesítjük előnyben.
        if cid not in valid_feeds:
            valid_feeds[cid] = feed
        elif feed.get("is_main"):
            valid_feeds[cid] = feed

    print(
        "Magyar országos feedek:",
        len(valid_feeds)
    )

    best = {}

    for stream in streams:
        cid = stream.get("channel")
        fid = stream.get("feed")

        if cid not in valid_feeds:
            continue

        feed = valid_feeds[cid]

        if fid != feed.get("id"):
            continue

        url = stream.get("url")

        if not url:
            continue

        q = quality(
            stream.get("quality")
        )

        old = best.get(cid)

        if old is None or q > old[0]:
            best[cid] = (
                q,
                stream
            )

    result = []

    for cid, data in best.items():
        channel = channel_map.get(cid)

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
            "url": stream.get("url"),
            "referrer": stream.get(
                "referrer"
            ),
            "user_agent": stream.get(
                "user_agent"
            )
        })

    result.sort(
        key=lambda x:
        x["name"].lower()
    )

    lines = ["#EXTM3U"]

    for item in result:

        extinf = (
            '#EXTINF:-1 '
            'tvg-country="HU" '
            'tvg-language="Hungarian" '
            'tvg-id="' + item["id"] + '" '
            'tvg-logo="' + item["logo"] + '",'
            + item["name"]
        )

        lines.append(extinf)

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
        "Elérhető országos magyar csatornák:",
        len(result)
    )

    print("magyar.m3u elkészült.")


if __name__ == "__main__":
    main()
