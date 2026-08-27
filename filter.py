import json
import urllib.request
from pathlib import Path


API = "https://iptv-org.github.io/api"
OUTPUT = Path("magyar.m3u")


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        return json.load(response)


def norm(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def quality(value):
    if not value:
        return 0

    digits = "".join(
        c for c in str(value)
        if c.isdigit()
    )

    return int(digits) if digits else 0


def is_hungarian(channel, feed):
    country = norm(channel.get("country"))

    if country != "hu":
        return False

    languages = {
        norm(x)
        for x in feed.get("languages", [])
    }

    return "hun" in languages


def is_religious(channel):
    categories = {
        norm(x)
        for x in channel.get("categories", [])
    }

    return "religious" in categories


def is_local_or_regional(feed):
    areas = {
        norm(x)
        for x in feed.get("broadcast_area", [])
    }

    # Csak országos magyar feed kell.
    if "c/hu" not in areas:
        return True

    # Az iptv-org területi jelölései:
    #
    # r/  = régió
    # s/  = állam / megye / tartomány jellegű terület
    # ct/ = város
    #
    # Ha ezek bármelyike szerepel az országos jelölés
    # mellett, helyi/regionális feedként kezeljük.

    for area in areas:

        if area.startswith("r/"):
            return True

        if area.startswith("s/"):
            return True

        if area.startswith("ct/"):
            return True

    return False


def suspicious_local_name(channel, feed):
    """
    Másodlagos biztonsági szűrő.

    Nem városneveket tartalmaz.
    Az egyértelmű helyi TV-elnevezéseket szűri.
    """

    names = []

    names.append(
        channel.get("name", "")
    )

    names.extend(
        channel.get("alt_names", [])
    )

    names.append(
        feed.get("name", "")
    )

    names.extend(
        feed.get("alt_names", [])
    )

    patterns = (
        "városi tv",
        "varosi tv",
        "városi televízió",
        "varosi televizio",
        "helyi tv",
        "helyi televízió",
        "helyi televizio",
        "regionális tv",
        "regionalis tv",
        "regionális televízió",
        "regionalis televizio",
        "régiós tv",
        "regios tv",
        "térségi tv",
        "tersegi tv",
        "megyei tv",
        "megyei televízió",
        "megyei televizio",
        "kerületi tv",
        "keruleti tv",
        "kerületi televízió",
        "keruleti televizio",
        "önkormányzati tv",
        "onkormanyzati tv",
        "önkormányzati televízió",
        "onkormanyzati televizio",
        "local tv",
        "local television",
        "community tv",
        "municipal tv",
    )

    for name in names:

        name = norm(name)

        for pattern in patterns:

            if pattern in name:
                return True

    return False


def main():

    print("IPTV-org adatok letöltése...")

    channels = get_json(
        f"{API}/channels.json"
    )

    feeds = get_json(
        f"{API}/feeds.json"
    )

    streams = get_json(
        f"{API}/streams.json"
    )

    logos = get_json(
        f"{API}/logos.json"
    )

    channels_by_id = {
        channel["id"]: channel
        for channel in channels
        if channel.get("id")
    }

    # ---------------------------------------------------------
    # LOGÓK
    # ---------------------------------------------------------

    logos_by_channel = {}

    for logo in logos:

        channel_id = logo.get("channel")

        if not channel_id:
            continue

        current = logos_by_channel.get(
            channel_id
        )

        if current is None:
            logos_by_channel[channel_id] = logo

        elif logo.get("in_use") is True:
            logos_by_channel[channel_id] = logo

    # ---------------------------------------------------------
    # FEED SZŰRÉS
    # ---------------------------------------------------------

    valid_feeds = []

    rejected_religious = 0
    rejected_local = 0
    rejected_language = 0
    rejected_country = 0

    for feed in feeds:

        channel_id = feed.get("channel")

        if not channel_id:
            continue

        channel = channels_by_id.get(
            channel_id
        )

        if not channel:
            continue

        # Magyarország
        if norm(channel.get("country")) != "hu":
            rejected_country += 1
            continue

        # Vallási
        if is_religious(channel):
            rejected_religious += 1
            continue

        # Magyar nyelv
        if not is_hungarian(channel, feed):
            rejected_language += 1
            continue

        # Regionális / megyei / városi
        if is_local_or_regional(feed):
            rejected_local += 1
            continue

        # Név alapján extra biztonsági ellenőrzés
        if suspicious_local_name(channel, feed):
            rejected_local += 1
            continue

        valid_feeds.append(feed)

    print(
        "Kizárt vallási:",
        rejected_religious
    )

    print(
        "Kizárt helyi/régiós:",
        rejected_local
    )

    print(
        "Kizárt nem magyar nyelv:",
        rejected_language
    )

    print(
        "Megfelelő feedek:",
        len(valid_feeds)
    )

    # ---------------------------------------------------------
    # STREAM-EK
    # ---------------------------------------------------------

    valid_keys = {
        (
            feed.get("channel"),
            feed.get("id")
        )
        for feed in valid_feeds
    }

    streams_by_feed = {}

    for stream in streams:

        key = (
            stream.get("channel"),
            stream.get("feed")
        )

        if key not in valid_keys:
            continue

        url = stream.get("url")

        if not url:
            continue

        streams_by_feed.setdefault(
            key,
            []
        ).append(stream)

    # ---------------------------------------------------------
    # LEGJOBB STREAM CSATORNÁNKÉNT
    # ---------------------------------------------------------

    result = {}

    for feed in valid_feeds:

        channel_id = feed.get("channel")
        feed_id = feed.get("id")

        channel = channels_by_id.get(
            channel_id
        )

        if not channel:
            continue

        available = streams_by_feed.get(
            (
                channel_id,
                feed_id
            ),
            []
        )

        if not available:
            continue

        available.sort(
            key=lambda x: (
                -quality(x.get("quality")),
                norm(x.get("label"))
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

        entry = {
            "id": channel_id,
            "name": name,
            "logo": logo,
            "url": str(
                stream.get("url")
            ),
            "referrer": str(
                stream.get("referrer")
                or ""
            ),
            "user_agent": str(
                stream.get("user_agent")
                or ""
            ),
            "quality": quality(
                stream.get("quality")
            )
        }

        old = result.get(
            channel_id
        )

        if old is None:
            result[channel_id] = entry

        elif entry["quality"] > old["quality"]:
            result[channel_id] = entry

    channels_result = list(
        result.values()
    )

    channels_result.sort(
        key=lambda x:
        norm(x["name"])
    )

    print(
        "Végleges csatornák:",
        len(channels_result)
    )

    # ---------------------------------------------------------
    # M3U
    # ---------------------------------------------------------

    lines = [
        "#EXTM3U",
        "# Magyar nyelvű országos TV csatornák",
        "# Vallási, regionális,
