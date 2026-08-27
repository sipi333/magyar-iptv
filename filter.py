
#!/usr/bin/env python3

import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")


# ============================================================
# KIZÁRANDÓ HELYI / REGIONÁLIS CSATORNÁK
# ============================================================

REGIONAL = [
    "bábolnai",
    "babolnai",
    "bajai tv",
    "balaton tv",
    "berente tv",
    "csurgó tv",
    "csurgo tv",
    "daru tv",
    "egykertv",
    "estv",
    "fehérvár tv",
    "fehervar tv",
    "globo tv",
    "gólya tv",
    "golya tv",
    "gyöngyösi tv",
    "gyongyosi tv",
    "hegyvidék tv",
    "hegyvidek tv",
    "hévíz tv",
    "hev iz tv",
    "kanizsa tv",
    "kanizsa",
    "kapos tv",
    "kaposvár tv",
    "kaposvar tv",
    "karcag tv",
    "kiskőrös tv",
    "kiskoros tv",
    "komáromi televízió",
    "komaromi televizio",
    "komló tv",
    "komlo tv",
    "mezőkövesdi televízió",
    "mezokovesdi televizio",
    "pilis tv",
    "rákosmente tv",
    "rakosmente tv",
    "szentendre tv",
    "tatai tv",
    "telepaks",
    "tisza tv",
    "tv eger",
    "tv keszthely",
    "vásárhelyi televízió",
    "vasarhelyi televizio",
    "völgyhíd tv",
    "volgyhid tv",
    "fuzesabony",
    "mór tv",
    "mor tv",
    "városi tv",
    "varosi tv",
    "városi televízió",
    "varosi televizio",
    "regionális",
    "regionalis",
    "region tv",
    "régió tv",
    "regio tv",
    "térségi tv",
    "tersegi tv",
    "megyei tv",
    "megyei televízió",
    "kerületi tv",
    "keruleti tv",
    "local tv",
]


# ============================================================
# KIZÁRANDÓ VALLÁSI CSATORNÁK
# ============================================================

RELIGIOUS = [
    "vallás",
    "vallas",
    "religious",
    "christian",
    "christ",
    "church",
    "gospel",
    "katolikus",
    "katol",
    "catholic",
    "református",
    "reformatus",
    "reformát",
    "evangélikus",
    "evangelikus",
    "evangé",
    "evangel",
    "biblia",
    "bible",
    "istentisztelet",
    "keresztény",
    "kereszteny",
    "hit gyülekezete",
]


# ============================================================
# RÁDIÓK KIZÁRÁSA
# ============================================================

RADIO = [
    "rádió",
    "radio",
    "fm radio",
]


# ============================================================
# NEM KÍVÁNT CSATORNÁK
# ============================================================

OTHER_EXCLUDED = [
    "babyfirst",
    "bbc earth",
    "ebs",
]


def download_playlist():

    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(request, timeout=60) as response:

        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def get_channels(text):

    lines = text.splitlines()

    channels = []

    current = []

    for line in lines:

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

        if line.startswith("#EXTINF"):

            if "," in line:

                return line.split(",", 1)[1].strip()

    return ""


def get_id(channel):

    for line in channel:

        match = re.search(
            r'tvg-id="([^"]+)"',
            line,
            re.IGNORECASE
        )

        if match:

            return match.group(1)

    return ""


def should_remove(channel):

    text = "\n".join(channel).lower()

    name = get_name(channel).lower()

    tvg_id = get_id(channel).lower()

    combined = text + " " + name + " " + tvg_id

    # Helyi / regionális
    for word in REGIONAL:

        if word in combined:

            return True

    # Vallási
    for word in RELIGIOUS:

        if word in combined:

            return True

    # Rádió
    for word in RADIO:

        if word in combined:

            return True

    # Egyéb kizárás
    for word in OTHER_EXCLUDED:

        if word in combined:

            return True

    return False


def main():

    print("IPTV lista letöltése...")

    source = download_playlist()

    channels = get_channels(source)

    print("Forrásban található csatornák:", len(channels))

    result = []

    seen = set()

    removed = 0
    duplicates = 0

    for channel in channels:

        if should_remove(channel):

            removed += 1

            continue

        name = get_name(channel)

        tvg_id = get_id(channel)

        key = tvg_id or name.lower()

        if key in seen:

            duplicates += 1

            continue

        seen.add(key)

        result.extend(channel)

    playlist = ["#EXTM3U"]

    playlist.extend(result)

    OUTPUT.write_text(
        "\n".join(playlist) + "\n",
        encoding="utf-8"
    )

    final_count = sum(
        1
        for line in playlist
        if line.startswith("#EXTINF")
    )

    print("")
    print("================================")
    print(" MAGYAR IPTV LISTA ELKÉSZÜLT")
    print("================================")
    print("Eredeti:", len(channels))
    print("Kiszűrve:", removed)
    print("Duplikáció:", duplicates)
    print("Végleges:", final_count)
    print("Fájl:", OUTPUT)
    print("================================")


if __name__ == "__main__":
    main()

