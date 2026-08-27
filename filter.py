#!/usr/bin/env python3

import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")

# Csak olyan csatornák, amelyeket országos/magyar tematikus
# csatornaként engedélyezünk.
ALLOWED = {
    "M1",
    "M2",
    "M4 Sport",
    "M5",
    "Duna",
    "Duna World",
    "RTL",
    "TV2",
    "ATV",
    "ATV Spirit",
    "Hír TV",
    "N1 TV",
    "Euronews",
    "Spektrum",
    "Spektrum Home",
    "National Geographic",
    "National Geographic Wild",
    "History",
    "Film+",
    "Film Cafe",
    "Film4",
    "Mozi+",
    "Moziverzum",
    "Izaura TV",
    "Jocky TV",
    "Cool",
    "RTL Gold",
    "RTL Kettő",
    "Sorozat+",
    "Viasat3",
    "Viasat6",
    "Life TV",
    "FEM3",
    "Galaxy4",
    "Hatoscsatorna",
    "Fix TV",
    "Muzsika TV",
    "Minimax",
    "Nickelodeon",
    "Nick Jr.",
    "Nicktoons",
    "Disney Channel",
}

# Ezek akkor is kiesnek, ha egy hasonló nevű csatorna
# véletlenül bekerülne a forráslistába.
EXCLUDED = (
    "városi",
    "varosi",
    "térségi",
    "tersegi",
    "regionális",
    "regionalis",
    "régió",
    "regio",
    "megyei",
    "kerületi",
    "keruleti",
    "helyi",
    "city tv",
    "local tv",
    "vallás",
    "vallas",
    "vallási",
    "vallasos",
    "religious",
    "christian",
    "gospel",
    "church",
    "catholic",
    "katolikus",
    "református",
    "reformatus",
    "evangélikus",
    "evangelikus",
    "biblia",
    "bible",
    "rádió",
    "radio",
)


def normalize(value):
    value = value.lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ö": "o",
        "ő": "o",
        "ú": "u",
        "ü": "u",
        "ű": "u",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"\s+", " ", value)
    return value.strip()


ALLOWED_NORMALIZED = {
    normalize(name) for name in ALLOWED
}

EXCLUDED_NORMALIZED = tuple(
    normalize(word) for word in EXCLUDED
)


def download_playlist():
    request = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def get_channels(text):
    channels = []
    current = []

    for line in text.splitlines():

        if line.startswith("#EXTINF"):

            if current:
                channels.append(current)

            current = [line]

        elif current:

            current.append(line)

    if current:
        channels.append(current)

    return channels


def get_name(channel):
    for line in channel:

        if line.startswith("#EXTINF") and "," in line:
            return line.split(",", 1)[1].strip()

    return ""


def is_allowed(name):

    normalized = normalize(name)

    # Először kizárjuk a helyi, regionális,
    # vallási és rádiós csatornákat.
    for word in EXCLUDED_NORMALIZED:

        if word in normalized:
            return False

    # Minőségi / egyéb jelölések eltávolítása.
    cleaned = re.sub(
        r"\s*(1080p|720p|576p|480p|360p)\s*$",
        "",
        normalized,
        flags=re.IGNORECASE
    ).strip()

    # Csak az engedélyezett csatornák maradhatnak.
    return cleaned in ALLOWED_NORMALIZED


def main():

    print("Magyar IPTV lista letöltése...")

    source = download_playlist()
    channels = get_channels(source)

    print("Forrásban található csatornák:", len(channels))

    result = ["#EXTM3U"]

    kept = 0
    removed = 0

    seen = set()

    for channel in channels:

        name = get_name(channel)

        if not is_allowed(name):
            removed += 1
            continue

        key = normalize(name)

        if key in seen:
            continue

        seen.add(key)

        result.extend(channel)
        kept += 1

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    print("")
    print("==============================")
    print(" MAGYAR IPTV")
    print("==============================")
    print("Forrás:", len(channels))
    print("Benne maradt:", kept)
    print("Kiszűrve:", removed)
    print("==============================")


if __name__ == "__main__":
    main()
