import json
import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
CHANNELS_API = "https://iptv-org.github.io/api/channels.json"

OUTPUT = Path("magyar.m3u")


# ============================================================
# FIXEN KIZÁRANDÓ HELYI / VÁROSI / RÉGIÓS CSATORNÁK
# ============================================================

EXCLUDE_IDS = {
    "16tvBudapest.hu",
    "AlfoldTV.hu",
    "BajaiTV.hu",
    "BalatonTV.hu",
    "BerenteTV.hu",
    "BudapestEuropaTelevizio.hu",
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
    "MakoiVarosiTV.hu",
    "MezokovesdiTelevizio.hu",
    "MoraNetTV.hu",
    "ObudaTV.hu",
    "OroszlanyiVarosiTelevizio.hu",
    "OzdiVarosiTV.hu",
    "PilisTV.hu",
    "PutnokVarosiTV.hu",
    "RakosmenteTV.hu",
    "RegioTV.hu",
    "RegioPluszTV.hu",
    "SoltvadkertiTelevizio.hu",
    "SzecsenyTV.hu",
    "SzolnokTV.hu",
    "TataiTV.hu",
    "TelePaks.hu",
    "TiszaTV.hu",
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

    # további gyakori helyi azonosítók
    "CityTV.hu",
    "TrimedioTV.hu",
}


# ============================================================
# VALLÁSI CSATORNÁK
# ============================================================

RELIGIOUS_IDS = {
    "ApostolTV.hu",
    "PaxTV.hu",
    "EWTN.hu",
    "BonumTV.hu",
    "EWTNBonumTV.hu",
}


RELIGIOUS_WORDS = (
    "apostol",
    "pax tv",
    "paxtv",
    "ewtn",
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
    "vallási",
    "vallasi",
    "religious",
)


# ============================================================
# HELYI / VÁROSI / RÉGIÓS NÉVMINTÁK
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
)


# ============================================================
# RÁDIÓ KIZÁRÁSA
# ============================================================

RADIO_WORDS = (
    "rádió",
    "radio",
)


# ============================================================
# LETÖLTÉS
# ============================================================

def download(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 IPTV Filter"
        },
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read().decode("utf-8", errors="replace")


# ============================================================
# NORMALIZÁLÁS
# ============================================================

def normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def base_id(channel_id):
    """
    Példa:

    BTV.hu@SD
    BTV.hu@HD

    mindkettőből:

    BTV.hu
    """

    return channel_id.split("@", 1)[0].strip()


def get_attr(line, name):
    match = re.search(
        rf'(?:^|\s){re.escape(name)}="([^"]*)"',
        line
    )

    return match.group(1) if match else ""


# ============================================================
# IPTV-ORG CSATORNA ADATBÁZIS
# ============================================================

def load_channels():

    print("IPTV-org csatorna-adatbázis letöltése...")

    text = download(CHANNELS_API)

    data = json.loads(text)

    channels = {}

    for channel in data:

        channel_id = str(
            channel.get("id", "")
        ).strip()

        if channel_id:
            channels[channel_id] = channel

    print(
        "IPTV-org adatbázis:",
        len(channels),
        "csatorna"
    )

    return channels


# ============================================================
# CSATORNA ELLENŐRZÉSE
# ============================================================

def should_exclude(info, channels):

    channel_id = get_attr(
        info,
        "tvg-id"
    )

    clean_id = base_id(channel_id)

    channel_name = info.split(
        ",",
        1
    )[-1].strip()

    group = get_attr(
        info,
        "group-title"
    )

    database = channels.get(
        clean_id,
        {}
    )

    db_name = database.get(
        "name",
        ""
    )

    alt_names = database.get(
        "alt_names",
        []
    )

    categories = database.get(
        "categories",
        []
    )

    if not isinstance(
        alt_names,
        list
    ):
        alt_names = []

    if not isinstance(
        categories,
        list
    ):
        categories = []

    check = normalize(
        " ".join(
            [
                clean_id,
                channel_name,
                group,
                db_name,
                " ".join(
                    str(x)
                    for x in alt_names
                ),
                " ".join(
                    str(x)
                    for x in categories
                ),
            ]
        )
    )

    # --------------------------------------------------------
    # FIX HELYI ID
    # --------------------------------------------------------

    if clean_id in EXCLUDE_IDS:
        return True

    # --------------------------------------------------------
    # FIX VALLÁSI ID
    # --------------------------------------------------------

    if clean_id in RELIGIOUS_IDS:
        return True

    # --------------------------------------------------------
    # IPTV-ORG RELIGIOUS KATEGÓRIA
    # --------------------------------------------------------

    category_values = {
        normalize(x)
        for x in categories
    }

    if "religious" in category_values:
        return True

    # --------------------------------------------------------
    # VALLÁSI KULCSSZAVAK
    # --------------------------------------------------------

    for word in RELIGIOUS_WORDS:

        if word in check:
            return True

    # --------------------------------------------------------
    # HELYI / VÁROSI / RÉGIÓS KULCSSZAVAK
    # --------------------------------------------------------

    for word in LOCAL_WORDS:

        if word in check:
            return True

    # --------------------------------------------------------
    # RÁDIÓ
    # --------------------------------------------------------

    for word in RADIO_WORDS:

        if word in check:
            return True

    return False


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print()
    print("======================================")
    print(" MAGYAR IPTV AUTOMATIKUS SZŰRŐ")
    print("======================================")
    print()

    channels = load_channels()

    print()
    print("Magyar IPTV lista letöltése...")

    text = download(SOURCE)

    lines = text.splitlines()

    output = [
        "#EXTM3U"
    ]

    total = 0
    excluded = 0
    kept = 0

    seen = set()

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line.startswith(
            "#EXTINF:"
        ):
            i += 1
            continue

        total += 1

        info = line

        url = ""

        extra_lines = []

        j = i + 1

        while j < len(lines):

            candidate = lines[j].strip()

            if (
                candidate
                and not candidate.startswith("#")
            ):
                url = candidate
                break

            if candidate:
                extra_lines.append(
                    lines[j]
                )

            j += 1

        channel_id = get_attr(
            info,
            "tvg-id"
        )

        channel_name = info.split(
            ",",
            1
        )[-1].strip()

        clean_id = base_id(
            channel_id
        )

        remove = False

        # ----------------------------------------------------
        # SZŰRÉS
        # ----------------------------------------------------

        if should_exclude(
            info,
            channels
        ):
            remove = True

        # ----------------------------------------------------
        # NINCS STREAM
        # ----------------------------------------------------

        if not url:
            remove = True

        # ----------------------------------------------------
        # DUPLIKÁCIÓ
        # ----------------------------------------------------

        key = normalize(
            clean_id
            or channel_name
        )

        if not key:
            remove = True

        elif key in seen:
            remove = True

        # ----------------------------------------------------
        # KIMENET
        # ----------------------------------------------------

        if remove:

            excluded += 1

            print(
                "KIZÁRVA:",
                channel_name
            )

        else:

            seen.add(key)

            output.append(info)

            for extra in extra_lines:
                output.append(extra)

            output.append(url)

            kept += 1

        i = j + 1

    # ========================================================
    # FÁJL MENTÉSE
    # ========================================================

    OUTPUT.write_text(
        "\n".join(output)
        + "\n",
        encoding="utf-8"
    )

    print()
    print("======================================")
    print(" EREDMÉNY")
    print("======================================")
    print(
        "Forrás:",
        total
    )
    print(
        "Kiszűrve:",
        excluded
    )
    print(
        "Megmaradt:",
        kept
    )
    print(
        "Kimenet:",
        OUTPUT
    )
    print("======================================")


if __name__ == "__main__":
    main()
