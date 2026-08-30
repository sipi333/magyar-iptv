import re
import urllib.request
from pathlib import Path

# Közvetlenül az IPTV-org aktuális magyar streamlistájából dolgozunk.
SOURCE = "https://iptv-org.github.io/iptv/streams/hu.m3u"
OUTPUT = Path("magyar.m3u")


# ============================================================
# KÜLÖN MEGTARTANDÓ CSATORNA
# ============================================================

KEEP_IDS = {
    "DunaWorld.hu",
}


# ============================================================
# KIZÁRANDÓ CSATORNÁK
# ============================================================

EXCLUDE_IDS = {

    # Városi / helyi / regionális
    "16tvBudapest.hu",
    "AlfoldTV.hu",
    "BTV.hu",
    "BajaiTV.hu",
    "BalatonTV.hu",
    "BerenteTV.hu",
    "BudapestEuropaTelevizio.hu",
    "CityTV.hu",
    "CsurgoTV.hu",
    "DaruTV.hu",
    "DTV.hu",
    "EgykerTV.hu",
    "ESTV.hu",
    "FehervarTV.hu",
    "GloboTV.hu",
    "GolyaTV.hu",
    "GyongyosiTV.hu",
    "HangulatTV.hu",
    "Hatoscsatorna.hu",
    "HegyvidekTV.hu",
    "HeviziTV.hu",
    "JaszsagiTersegiTV.hu",
    "KanizsaTV.hu",
    "KaposTV.hu",
    "KarcagTV.hu",
    "KecskemetiTV.hu",
    "KiskorosTV.hu",
    "KomaromiTelevizio.hu",
    "KomlosTV.hu",
    "LiceumTV.hu",
    "MakoiVarosiTelevizio.hu",
    "MezokovesdiTelevizio.hu",
    "MoraNetTV.hu",
    "ObudaTV.hu",
    "OroszlanyiVarosiTelevizio.hu",
    "OzdiVarosiTV.hu",
    "PilisTV.hu",
    "PutnokVarosiTV.hu",
    "RakovszkyTV.hu",
    "RakosmenteTV.hu",
    "RegioTV.hu",
    "RegioPluszTV.hu",
    "SoltvadkertiTelevizio.hu",
    "SzecsenyTV.hu",
    "SzolnokTV.hu",
    "TataiTV.hu",
    "TelePaks.hu",
    "TiszaTV.hu",
    "TrimedioTV.hu",
    "TV7Bekescsaba.hu",
    "TVBudakalasz.hu",
    "TVEger.hu",
    "TVKeszthely.hu",
    "TVSzentendre.hu",
    "VasarhelyiTelevizio.hu",
    "VolgyhidTV.hu",
    "VTVFuzesabony.hu",
    "VTVMor.hu",
    "XVTV.hu",
    "ZalaegerszegiTV.hu",
    "ZugloTV.hu",

    # Külön kért kizárások
    "OrszaggyulesOGYplenaris.hu",
    "OrszaggyulesOGYTAB.hu",
    "WilliamsTV.hu",
}


# ============================================================
# VALLÁSI CSATORNÁK
# ============================================================

RELIGIOUS_WORDS = (
    "apostol",
    "pax",
    "ewtn",
    "bonum",
    "katolikus",
    "catholic",
    "reformatus",
    "református",
    "evangelikus",
    "evangélikus",
    "kereszteny",
    "keresztény",
    "christian",
    "gospel",
    "church",
    "biblia",
    "bible",
    "vallasi",
    "vallási",
    "religious",
)


# ============================================================
# HELYI / VÁROSI / RÉGIÓS KULCSSZAVAK
# ============================================================

LOCAL_WORDS = (
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
    "régiós televízió",
    "regios televizio",
    "térségi tv",
    "tersegi tv",
    "térségi televízió",
    "tersegi televizio",
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
    "közösségi tv",
    "kozossegi tv",
    "local tv",
    "localtv",
    "city tv",
    "citytv",
)


# ============================================================
# RÁDIÓ
# ============================================================

RADIO_WORDS = (
    "rádió",
    "radio",
)


# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def download(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 IPTV Filter"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=180
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_attr(line, name):
    match = re.search(
        rf'(?:^|\s){re.escape(name)}="([^"]*)"',
        line
    )

    return match.group(1) if match else ""


def clean_id(channel_id):
    return channel_id.split("@", 1)[0].strip()


# ============================================================
# SZŰRÉS
# ============================================================

def should_remove(info):

    channel_id = get_attr(info, "tvg-id")
    group = get_attr(info, "group-title")
    name = info.split(",", 1)[-1].strip()

    base_channel_id = clean_id(channel_id)

    # Duna World mindig maradjon,
    # ha az IPTV-org forrás tartalmazza.
    if base_channel_id in KEEP_IDS:
        return False

    check = normalize(
        " ".join([
            channel_id,
            base_channel_id,
            name,
            group,
        ])
    )

    # Fixen kizárt csatornák
    if base_channel_id in EXCLUDE_IDS:
        return True

    # Helyi / városi / regionális
    for word in LOCAL_WORDS:
        if normalize(word) in check:
            return True

    # Vallási
    for word in RELIGIOUS_WORDS:
        if normalize(word) in check:
            return True

    # Rádió
    for word in RADIO_WORDS:
        if normalize(word) in check:
            return True

    return False


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print("Magyar IPTV lista letöltése...")
    print("Forrás:", SOURCE)

    text = download(SOURCE)
    lines = text.splitlines()

    result = ["#EXTM3U"]

    total = 0
    excluded = 0
    kept = 0

    seen = set()
    duna_world_found = False

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line.startswith("#EXTINF:"):
            i += 1
            continue

        total += 1

        info = line
        url = ""

        j = i + 1

        # Megkeressük az EXTINF utáni stream URL-t.
        while j < len(lines):

            candidate = lines[j].strip()

            if candidate and not candidate.startswith("#"):
                url = candidate
                break

            j += 1

        name = info.split(",", 1)[-1].strip()
        channel_id = get_attr(info, "tvg-id")
        base_channel_id = clean_id(channel_id)

        key = normalize(
            base_channel_id or name
        )

        remove = False

        if not url:
            remove = True

        elif not key:
            remove = True

        elif key in seen:
            remove = True

        elif should_remove(info):
            remove = True

        if remove:

            excluded += 1
            print("KISZŰRVE:", name)

        else:

            seen.add(key)

            result.append(info)
            result.append(url)

            kept += 1

            if base_channel_id == "DunaWorld.hu":
                duna_world_found = True
                print("MEGTARTVA: Duna World")

        i = j + 1

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    print()
    print("==============================")
    print("Forrás:", total)
    print("Kiszűrve:", excluded)
    print("Megmaradt:", kept)
    print(
        "Duna World:",
        "MEGTALÁLVA ÉS MEGTARTVA"
        if duna_world_found
        else "NEM TALÁLHATÓ A FORRÁSBAN"
    )
    print("==============================")


if __name__ == "__main__":
    main()
