```python
#!/usr/bin/env python3

import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")

# ============================================================
# ENGEDÉLYEZETT MAGYAR / ORSZÁGOS CSATORNÁK
# ============================================================

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


# ============================================================
# KIZÁRT KIFEJEZÉSEK
# ============================================================

EXCLUDED = (
    # helyi / regionális
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
    "citytv",
    "local tv",
    "localtv",

    # vallási
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

    # rádió
    "rádió",
    "radio",
)


# ============================================================
# NORMALIZÁLÁS
# ============================================================

def normalize(value):
    value = value.lower().strip()

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
    normalize(name)
    for name in ALLOWED
}

EXCLUDED_NORMALIZED = tuple(
    normalize(word)
    for word in EXCLUDED
)


# ============================================================
# PLAYLIST LETÖLTÉSE
# ============================================================

def download_playlist():

    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        return response.read().decode(
            "utf-8",
            errors="replace"
        )


# ============================================================
# CSATORNÁK FELDOLGOZÁSA
# ============================================================

def get_channels(text):

    channels = []
    current = []

    for line in text.splitlines():

        line = line.strip()

        if line.startswith("#EXTINF"):

            if current:
                channels.append(current)

            current = [line]

        elif current:

            current.append(line)

    if current:
        channels.append(current)

    return channels


# ============================================================
# CSATORNANÉV KINYERÉSE
# ============================================================

def get_name(channel):

    for line in channel:

        if line.startswith("#EXTINF") and "," in line:

            return line.split(",", 1)[1].strip()

    return ""


# ============================================================
# NÉV TISZTÍTÁSA
# ============================================================

def clean_name(name):

    name = normalize(name)

    # Gyakori technikai jelölések eltávolítása
    suffix_pattern = (
        r"\s*"
        r"(1080p|720p|576p|480p|360p|"
        r"1080i|720i|576i|480i|"
        r"uhd|fhd|hd|sd)"
        r"\s*$"
    )

    name = re.sub(
        suffix_pattern,
        "",
        name,
        flags=re.IGNORECASE
    )

    # Záró kötőjelek / felesleges szóközök
    name = re.sub(
        r"\s*[-|]\s*$",
        "",
        name
    )

    return name.strip()


# ============================================================
# ENGEDÉLYEZÉS
# ============================================================

def is_allowed(name):

    normalized = normalize(name)

    # ----------------------------------------
    # KIZÁRT KIFEJEZÉSEK
    # ----------------------------------------

    for word in EXCLUDED_NORMALIZED:

        if word in normalized:
            return False

    # ----------------------------------------
    # CSATORNANÉV TISZTÍTÁSA
    # ----------------------------------------

    cleaned = clean_name(name)

    # ----------------------------------------
    # CSAK PONTOS EGYEZÉS
    # ----------------------------------------

    return cleaned in ALLOWED_NORMALIZED


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print("Magyar IPTV lista letöltése...")
    print("")

    try:

        source = download_playlist()

    except Exception as error:

        print("HIBA: nem sikerült letölteni a forráslistát.")
        print(error)

        return

    channels = get_channels(source)

    print(
        "Forrásban található csatornák:",
        len(channels)
    )

    result = ["#EXTM3U"]

    kept = 0
    removed = 0
    duplicates = 0

    seen = set()

    for channel in channels:

        name = get_name(channel)

        if not name:

            removed += 1
            continue

        # ------------------------------------
        # SZŰRÉS
        # ------------------------------------

        if not is_allowed(name):

            removed += 1
            continue

        # ------------------------------------
        # DUPLIKÁCIÓ
        # ------------------------------------

        key = clean_name(name)

        if key in seen:

            duplicates += 1
            continue

        seen.add(key)

        result.extend(channel)

        kept += 1

    # ----------------------------------------
    # FÁJL MENTÉSE
    # ----------------------------------------

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    # ----------------------------------------
    # EREDMÉNY
    # ----------------------------------------

    print("")
    print("==============================")
    print(" MAGYAR IPTV")
    print("==============================")
    print("Forrás:", len(channels))
    print("Benne maradt:", kept)
    print("Kiszűrve:", removed)
    print("Duplikátum:", duplicates)
    print("==============================")
    print("")
    print("Készült:", OUTPUT)


if __name__ == "__main__":
    main()
```
