```python
#!/usr/bin/env python3

import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUT = Path("magyar.m3u")


# ============================================================
# KIZÁRANDÓ REGIONÁLIS / HELYI CSATORNÁK
# ============================================================

REGIONAL_WORDS = [
    "városi tv",
    "varosi tv",
    "városi televízió",
    "varosi televizio",
    "kerületi tv",
    "keruleti tv",
    "térségi tv",
    "tersegi tv",
    "regionális tv",
    "regionalis tv",
    "region tv",
    "régió tv",
    "regio tv",
    "régióplusz",
    "regioplusz",
    "megyei tv",
    "megyei televízió",
    "county tv",
    "local tv",
    "local television",
]


# Konkrét helyi/regionális csatornák azonosítói.
# Ha az iptv-org később új néven adja őket, a fenti
# regionális kifejezések is segítenek kiszűrni őket.

REGIONAL_IDS = {
    "BTV.hu@SD",
    "BajaiTV.hu@SD",
    "BalatonTV.hu@SD",
    "BerenteTV.hu@SD",
    "CsurgoTV.hu@SD",
    "DaruTV.hu@SD",
    "EgykerTV.hu@SD",
    "ESTV.hu@SD",
    "FehervarTV.hu@SD",
    "GloboTV.hu@SD",
    "GolyaTV.hu@SD",
    "GyongyosiTV.hu@SD",
    "HegyvidekTV.hu@SD",
    "HeviziTV.hu@SD",
    "JaszsagiTersegiTV.hu@SD",
    "KanizsaTV.hu@SD",
    "KaposTV.hu@SD",
    "KarcagTV.hu@SD",
    "KiskorosTV.hu@SD",
    "KomaromiTelevizio.hu@SD",
    "KomlosTV.hu@SD",
    "MezokovesdiTelevizio.hu@SD",
    "MoraNetTV.hu@SD",
    "PilisTV.hu@SD",
    "RakosmenteTV.hu@SD",
    "RegioTV.sk@SD",
    "RegioPluszTV.hu@SD",
    "SzecsenyTV.hu@SD",
    "TataiTV.hu@SD",
    "TelePaks.hu@SD",
    "TiszaTV.hu@SD",
    "TrimedioTV.hu@SD",
    "TVBudakalasz.hu@SD",
    "TVEger.hu@SD",
    "TVKeszthely.hu@SD",
    "TVSzentendre.hu@SD",
    "VasarhelyiTelevizio.hu@SD",
    "VolgyhidTV.hu@SD",
    "VTVFuzesabony.hu@SD",
    "VTVMor.hu@SD",
}


# ============================================================
# VALLÁSI / EGYHÁZI CSATORNÁK
# ============================================================

RELIGIOUS_WORDS = [
    "vallás",
    "vallas",
    "relig",
    "religious",
    "christ",
    "christian",
    "church",
    "gospel",
    "katol",
    "catholic",
    "reformát",
    "reformat",
    "reformatus",
    "evangé",
    "evange",
    "evangel",
    "biblia",
    "bible",
    "prédik",
    "predik",
    "istentisztelet",
    "zsidó",
    "zsido",
    "jewish",
    "muslim",
    "islam",
    "iszlám",
    "iszlam",
]


# ============================================================
# RÁDIÓK
# ============================================================

RADIO_WORDS = [
    "radio",
    "rádió",
    "radio",
    "fm radio",
]


# ============================================================
# NEM KÍVÁNT TARTALOM
# ============================================================

EXCLUDED_WORDS = [
    "babyfirst",
    "bbc earth",
    "ebs",
    "ebs plus",
    "euronews",
]


# ============================================================
# NEM ORSZÁGOS / PARLAMENTI / ÖNKORMÁNYZATI
# ============================================================

PUBLIC_LOCAL_WORDS = [
    "országgyűlés",
    "orszaggyules",
    "plenáris",
    "plenar",
    "törvényalkotási bizottság",
    "torvenyalkotasi bizottsag",
    "önkormányzat",
    "onkormanyzat",
]


def download(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def extract_tvg_id(block):
    match = re.search(
        r'tvg-id="([^"]+)"',
        block,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1)

    return ""


def extract_channel_name(block):
    """
    Az EXTINF sor vessző utáni részét használjuk
    a csatorna nevének meghatározására.
    """

    for line in block.splitlines():

        if line.startswith("#EXTINF"):

            if "," in line:
                return line.split(",", 1)[1].strip()

    return ""


def is_regional(block):

    tvg_id = extract_tvg_id(block)

    if tvg_id in REGIONAL_IDS:
        return True

    text = block.lower()

    for word in REGIONAL_WORDS:

        if word in text:
            return True

    return False


def is_religious(block):

    text = block.lower()

    for word in RELIGIOUS_WORDS:

        if word in text:
            return True

    return False


def is_radio(block):

    text = block.lower()

    for word in RADIO_WORDS:

        if word in text:
            return True

    return False


def is_excluded(block):

    text = block.lower()

    for word in EXCLUDED_WORDS:

        if word in text:
            return True

    return False


def is_public_local(block):

    text = block.lower()

    for word in PUBLIC_LOCAL_WORDS:

        if word in text:
            return True

    return False


def is_allowed(block):

    if is_regional(block):
        return False

    if is_religious(block):
        return False

    if is_radio(block):
        return False

    if is_excluded(block):
        return False

    if is_public_local(block):
        return False

    return True


def parse_playlist(text):

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


def channel_key(block):

    tvg_id = extract_tvg_id(block)

    name = extract_channel_name(block).lower()

    return tvg_id or name


def main():

    print("Downloading:", SOURCE)

    source = download(SOURCE)

    channels = parse_playlist(source)

    print("Source channels:", len(channels))

    output = []

    seen = set()

    removed_regional = 0
    removed_religious = 0
    removed_radio = 0
    removed_other = 0
    duplicates = 0

    for channel in channels:

        block = "\n".join(channel)

        if not is_allowed(block):

            if is_regional(block):
                removed_regional += 1

            elif is_religious(block):
                removed_religious += 1

            elif is_radio(block):
                removed_radio += 1

            else:
                removed_other += 1

            continue

        key = channel_key(block)

        if key in seen:

            duplicates += 1

            continue

        seen.add(key)

        output.extend(channel)

    final_playlist = [
        "#EXTM3U"
    ]

    final_playlist.extend(output)

    OUT.write_text(
        "\n".join(final_playlist) + "\n",
        encoding="utf-8"
    )

    channel_count = sum(
        1
        for line in final_playlist
        if line.startswith("#EXTINF")
    )

    print("")
    print("====================================")
    print(" Hungarian IPTV playlist generated")
    print("====================================")
    print("Final channels:", channel_count)
    print("Removed regional:", removed_regional)
    print("Removed religious:", removed_religious)
    print("Removed radio:", removed_radio)
    print("Removed other:", removed_other)
    print("Removed duplicates:", duplicates)
    print("Output:", OUT)
    print("====================================")


if __name__ == "__main__":
    main()
```
