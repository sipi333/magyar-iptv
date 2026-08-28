import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
SPORTS_SOURCE = "https://iptv-org.github.io/iptv/categories/sports.m3u"
OUTPUT = Path("magyar.m3u")

# ============================================================
# SPORTCSATORNÁK
# ============================================================

ALLOWED_SPORT_NAMES = (
    "fifa+",
    "fifa plus",
    "fifa+ women",
    "fifa plus women",
    "sky sports f1",
    "sport 1 baltic",
    "sport 5",
)

ALLOWED_SPORT_IDS = set()

# ============================================================
# FIXEN KIZÁRANDÓ HELYI / VÁROSI / RÉGIÓS CSATORNÁK
# ============================================================

EXCLUDE_IDS = {
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
        headers={"User-Agent": "Mozilla/5.0 IPTV Filter"}
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
# MAGYAR SZŰRÉS
# ============================================================

def should_remove(info):

    channel_id = get_attr(info, "tvg-id")
    group = get_attr(info, "group-title")
    name = info.split(",", 1)[-1].strip()

    original_id = normalize(channel_id)
    base_channel_id = normalize(clean_id(channel_id))

    check = normalize(
        " ".join([
            original_id,
            base_channel_id,
            name,
            group,
        ])
    )

    if clean_id(channel_id) in EXCLUDE_IDS:
        return True

    if base_channel_id in {
        normalize(x) for x in EXCLUDE_IDS
    }:
        return True

    for word in LOCAL_WORDS:
        if normalize(word) in check:
            return True

    for word in RELIGIOUS_WORDS:
        if normalize(word) in check:
            return True

    for word in RADIO_WORDS:
        if normalize(word) in check:
            return True

    return False


# ============================================================
# M3U BLOKKOK FELDOLGOZÁSA
# ============================================================

def parse_entries(text):

    lines = text.splitlines()
    entries = []

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line.startswith("#EXTINF:"):
            i += 1
            continue

        info = line
        url = ""

        j = i + 1

        while j < len(lines):

            candidate = lines[j].strip()

            if candidate and not candidate.startswith("#"):
                url = candidate
                break

            j += 1

        entries.append((info, url))

        i = j + 1

    return entries


# ============================================================
# SPORTCSATORNA ENGEDÉLYEZÉSE
# ============================================================

def is_allowed_sport(info):

    channel_id = get_attr(info, "tvg-id")
    group = get_attr(info, "group-title")
    name = info.split(",", 1)[-1].strip()

    check = normalize(
        " ".join([
            channel_id,
            clean_id(channel_id),
            name,
            group,
        ])
    )

    # Pontos ID, ha később hozzáadunk ilyet
    if clean_id(channel_id) in ALLOWED_SPORT_IDS:
        return True

    # Név/csoport alapú engedélyezés
    for allowed in ALLOWED_SPORT_NAMES:
        if normalize(allowed) in check:
            return True

    return False


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print("Magyar IPTV lista letöltése...")

    text = download(SOURCE)

    print("Sport IPTV lista letöltése...")

    sports_text = download(SPORTS_SOURCE)

    lines = text.splitlines()

    sport_entries = parse_entries(
        sports_text
    )

    result = ["#EXTM3U"]

    total = 0
    excluded = 0
    kept = 0
    sports_added = 0

    seen = set()

    i = 0

    # ========================================================
    # MAGYAR LISTA
    # ========================================================

    while i < len(lines):

        line = lines[i].strip()

        if not line.startswith("#EXTINF:"):
            i += 1
            continue

        total += 1

        info = line
        url = ""

        j = i + 1

        while j < len(lines):

            candidate = lines[j].strip()

            if candidate and not candidate.startswith("#"):
                url = candidate
                break

            j += 1

        name = info.split(",", 1)[-1].strip()
        channel_id = get_attr(info, "tvg-id")

        key = normalize(
            clean_id(channel_id) or name
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

            print(
                "KISZŰRVE:",
                name
            )

        else:

            seen.add(key)

            result.append(info)
            result.append(url)

            kept += 1

        i = j + 1

    # ========================================================
    # KIVÁLASZTOTT SPORTCSATORNÁK
    # ========================================================

    for info, url in sport_entries:

        if not url:
            continue

        if not is_allowed_sport(info):
            continue

        channel_id = clean_id(
            get_attr(info, "tvg-id")
        )

        name = info.split(",", 1)[-1].strip()

        key = normalize(
            channel_id or name
        )

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)

        result.append(info)
        result.append(url)

        sports_added += 1

        print(
            "SPORT HOZZÁADVA:",
            name
        )

    # ========================================================
    # KIMENET
    # ========================================================

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    print()
    print("==============================")
    print("Magyar forrás:", total)
    print("Magyar kiszűrve:", excluded)
    print("Magyar megmaradt:", kept)
    print("Sport hozzáadva:", sports_added)
    print(
        "Összes végső csatorna:",
        kept + sports_added
    )
    print("==============================")


if __name__ == "__main__":
    main()
