```python
#!/usr/bin/env python3

import re
import urllib.request
from pathlib import Path
from unicodedata import normalize as unicode_normalize


SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")


# ============================================================
# KIZÁRT KIFEJEZÉSEK
# ============================================================

EXCLUDED = (
    # --------------------------------------------------------
    # VÁROSI / HELYI / RÉGIÓS
    # --------------------------------------------------------
    "városi",
    "varosi",
    "térségi",
    "tersegi",
    "regionális",
    "regionalis",
    "régiós",
    "regios",
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
    "municipal",
    "district tv",

    # --------------------------------------------------------
    # VALLÁSI
    # --------------------------------------------------------
    "vallási",
    "vallas",
    "vallás",
    "vallásos",
    "vallasos",
    "religious",
    "christian",
    "christian tv",
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
    "jesus",
    "jézus",
    "jezus",

    # --------------------------------------------------------
    # RÁDIÓ
    # --------------------------------------------------------
    "rádió",
    "radio",
)


# ============================================================
# NORMALIZÁLÁS
# ============================================================

def normalize(value):
    value = value.lower().strip()

    value = unicode_normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not (
            0x300 <= ord(char) <= 0x36F
        )
    )

    value = re.sub(r"\s+", " ", value)

    return value.strip()


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
# EXTINF SOR
# ============================================================

def get_extinf(channel):

    for line in channel:

        if line.startswith("#EXTINF"):

            return line

    return ""


# ============================================================
# CSATORNANÉV
# ============================================================

def get_name(channel):

    extinf = get_extinf(channel)

    if not extinf:
        return ""

    if "," not in extinf:
        return ""

    return extinf.split(",", 1)[1].strip()


# ============================================================
# METAADATOK
# ============================================================

def get_attribute(extinf, attribute):

    pattern = rf'{re.escape(attribute)}="([^"]*)"'

    match = re.search(
        pattern,
        extinf,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return ""


def get_group(channel):

    extinf = get_extinf(channel)

    return get_attribute(
        extinf,
        "group-title"
    )


def get_categories(channel):

    extinf = get_extinf(channel)

    categories = []

    value = get_attribute(
        extinf,
        "group-title"
    )

    if value:
        categories.append(value)

    value = get_attribute(
        extinf,
        "category"
    )

    if value:
        categories.append(value)

    return " ".join(categories)


# ============================================================
# NÉV TISZTÍTÁSA
# ============================================================

def clean_name(name):

    name = normalize(name)

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

    name = re.sub(
        r"\s*[-|]\s*$",
        "",
        name
    )

    return name.strip()


# ============================================================
# SZÖVEG ELLENŐRZÉSE
# ============================================================

def contains_excluded(text):

    normalized = normalize(text)

    for word in EXCLUDED_NORMALIZED:

        if word in normalized:
            return True

    return False


# ============================================================
# RÉGIÓS / HELYI ELLENŐRZÉS
# ============================================================

def is_local_or_regional(name, group):

    text = f"{name} {group}"

    if contains_excluded(text):
        return True

    normalized = normalize(text)

    # Gyakori helyi/régiós TV elnevezések.
    regional_patterns = (
        r"\bmegye\b",
        r"\bmegyei\b",
        r"\btérség\b",
        r"\btérségi\b",
        r"\bregio\b",
        r"\bregional\b",
        r"\bregionális\b",
        r"\bváros\b",
        r"\bvárosi\b",
        r"\bhelyi\b",
        r"\blocal\b",
        r"\bcity\s*tv\b",
        r"\bkerület\b",
        r"\bkerületi\b",
    )

    for pattern in regional_patterns:

        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE
        ):
            return True

    return False


# ============================================================
# VALLÁSI ELLENŐRZÉS
# ============================================================

def is_religious(name, group):

    text = f"{name} {group}"

    return contains_excluded(text)


# ============================================================
# RÁDIÓ ELLENŐRZÉS
# ============================================================

def is_radio(name, group):

    text = f"{name} {group}"

    normalized = normalize(text)

    return (
        "rádió" in text.lower()
        or "radio" in normalized
        or re.search(r"\bradio\b", normalized)
        is not None
    )


# ============================================================
# CSATORNA SZŰRÉSE
# ============================================================

def is_allowed(channel):

    name = get_name(channel)

    if not name:
        return False, "nincs név"

    group = get_group(channel)

    # --------------------------------------------------------
    # RÁDIÓ
    # --------------------------------------------------------

    if is_radio(name, group):
        return False, "rádió"

    # --------------------------------------------------------
    # VALLÁSI
    # --------------------------------------------------------

    if is_religious(name, group):
        return False, "vallási"

    # --------------------------------------------------------
    # VÁROSI / HELYI / RÉGIÓS
    # --------------------------------------------------------

    if is_local_or_regional(name, group):
        return False, "helyi/régiós"

    # --------------------------------------------------------
    # MINDEN MÁS MAGYAR CSATORNA MEGMARAD
    # --------------------------------------------------------

    return True, "megtartva"


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print("Magyar IPTV lista letöltése...")
    print("Forrás:", SOURCE)
    print("")

    try:

        source = download_playlist()

    except Exception as error:

        print(
            "HIBA: nem sikerült letölteni "
            "a forráslistát."
        )

        print(error)

        raise SystemExit(1)

    channels = get_channels(source)

    print(
        "Forrásban található csatornák:",
        len(channels)
    )

    result = [
        "#EXTM3U"
    ]

    kept = 0
    removed = 0
    duplicates = 0

    removed_radio = 0
    removed_religious = 0
    removed_regional = 0

    seen = set()

    for channel in channels:

        name = get_name(channel)

        if not name:

            removed += 1
            continue

        allowed, reason = is_allowed(
            channel
        )

        if not allowed:

            removed += 1

            if reason == "rádió":
                removed_radio += 1

            elif reason == "vallási":
                removed_religious += 1

            elif reason == "helyi/régiós":
                removed_regional += 1

            continue

        # ----------------------------------------------------
        # DUPLIKÁCIÓ
        # ----------------------------------------------------

        key = clean_name(name)

        if key in seen:

            duplicates += 1
            continue

        seen.add(key)

        result.extend(channel)

        kept += 1

    # ========================================================
    # MENTÉS
    # ========================================================

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    # ========================================================
    # EREDMÉNY
    # ========================================================

    print("")
    print("==============================")
    print(" MAGYAR IPTV")
    print("==============================")

    print(
        "Forrás:",
        len(channels)
    )

    print(
        "Benne maradt:",
        kept
    )

    print(
        "Kiszűrve:",
        removed
    )

    print(
        " - rádió:",
        removed_radio
    )

    print(
        " - vallási:",
        removed_religious
    )

    print(
        " - helyi/régiós:",
        removed_regional
    )

    print(
        "Duplikátum:",
        duplicates
    )

    print("==============================")
    print("")
    print(
        "Készült:",
        OUTPUT
    )


if __name__ == "__main__":
    main()
```
