import csv
import io
import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
DATABASE = "https://raw.githubusercontent.com/iptv-org/database/master/data/channels.csv"
OUTPUT = Path("magyar.m3u")


# ============================================================
# KIFEJEZETTEN KIZÁRANDÓ HELYI / VÁROSI / RÉGIÓS CSATORNÁK
# Az @SD / @HD végét a program automatikusan levágja.
# ============================================================

EXCLUDE_IDS = {
    "BTV.hu",
    "AlfoldTV.hu",
    "BajaiTV.hu",
    "BalatonTV.hu",
    "BerenteTV.hu",
    "BudapestEuropaTelevizio.hu",
    "CsurgoTV.hu",
    "DaruTV.hu",
    "EgykerTV.hu",
    "ESTV.hu",
    "FehervarTV.hu",
    "GloboTV.hu",
    "GolyaTV.hu",
    "GyongyosiTV.hu",
    "HangulatTV.hu",
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
    "MakoiVarosiTV.hu",
    "MezokovesdiTelevizio.hu",
    "MoraNetTV.hu",
    "ObudaTV.hu",
    "OroszlanyiVarosiTelevizio.hu",
    "OzdiVarosiTV.hu",
    "PilisTV.hu",
    "PVTV.hu",
    "RakosmenteTV.hu",
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
}


# ============================================================
# HELYI / RÉGIÓS NÉVMINTÁK
# ============================================================

LOCAL_PATTERNS = [
    r"\bvárosi\s+tv\b",
    r"\bvarosi\s+tv\b",
    r"\bvárosi\s+televízió\b",
    r"\bvarosi\s+televizio\b",

    r"\bhelyi\s+tv\b",
    r"\bhelyi\s+televízió\b",
    r"\bhelyi\s+televizio\b",

    r"\bregionális\s+tv\b",
    r"\bregionalis\s+tv\b",
    r"\bregionális\s+televízió\b",
    r"\bregionalis\s+televizio\b",

    r"\brégiós\s+tv\b",
    r"\bregios\s+tv\b",
    r"\brégiós\s+televízió\b",
    r"\bregios\s+televizio\b",

    r"\btérségi\s+tv\b",
    r"\btersegi\s+tv\b",
    r"\btérségi\s+televízió\b",
    r"\btersegi\s+televizio\b",

    r"\bmegyei\s+tv\b",
    r"\bmegyei\s+televízió\b",
    r"\bmegyei\s+televizio\b",

    r"\bkerületi\s+tv\b",
    r"\bkeruleti\s+tv\b",
    r"\bkerületi\s+televízió\b",
    r"\bkeruleti\s+televizio\b",

    r"\bönkormányzati\s+tv\b",
    r"\bonkormanyzati\s+tv\b",

    r"\bközösségi\s+tv\b",
    r"\bkozossegi\s+tv\b",
]


# ============================================================
# VALLÁSI CSATORNÁK
# ============================================================

RELIGIOUS_WORDS = [
    "apostol",
    "pax tv",
    "paxtv",
    "ewtn",
    "bonum",
    "gran tv",
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
]


# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def download(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read().decode("utf-8", errors="replace")


def get_attr(line, name):
    match = re.search(
        rf'(?:^|\s){re.escape(name)}="([^"]*)"',
        line
    )
    return match.group(1) if match else ""


def normalize(text):
    text = str(text or "").lower()
    text = text.replace("ő", "ö")
    text = text.replace("ű", "ü")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def base_id(channel_id):
    """
    IPTV-org ID:
    BTV.hu@SD
    BTV.hu@HD

    Mindkettőből:
    BTV.hu
    """
    return channel_id.split("@", 1)[0].strip()


# ============================================================
# IPTV-ORG ADATBÁZIS
# ============================================================

def load_database():
    print("IPTV-org adatbázis letöltése...")

    text = download(DATABASE)

    database = {}

    reader = csv.DictReader(io.StringIO(text))

    for row in reader:
        channel_id = row.get("id", "").strip()

        if channel_id:
            database[channel_id] = row

    print("Adatbázis rekordok:", len(database))

    return database


# ============================================================
# CSATORNA SZŰRÉSE
# ============================================================

def should_exclude(info, database):

    channel_id = get_attr(info, "tvg-id")
    channel_name = info.split(",", 1)[-1].strip()
    group = get_attr(info, "group-title")

    clean_id = base_id(channel_id)

    db = database.get(clean_id, {})

    db_name = db.get("name", "")
    categories = db.get("categories", "")

    check = normalize(
        " ".join([
            clean_id,
            channel_name,
            group,
            db_name,
            categories
        ])
    )

    # --------------------------------------------------------
    # FIX ID
    # --------------------------------------------------------

    if clean_id in EXCLUDE_IDS:
        return True, "helyi csatorna - fix ID"

    # --------------------------------------------------------
    # RELIGIOUS KATEGÓRIA
    # --------------------------------------------------------

    category_list = [
        normalize(x)
        for x in re.split(r"[;,]", categories)
        if x.strip()
    ]

    if "religious" in category_list:
        return True, "vallási kategória"

    # --------------------------------------------------------
    # VALLÁSI NÉV
    # --------------------------------------------------------

    for word in RELIGIOUS_WORDS:
        if word in check:
            return True, "vallási csatorna"

    # --------------------------------------------------------
    # HELYI / RÉGIÓS NÉV
    # --------------------------------------------------------

    for pattern in LOCAL_PATTERNS:
        if re.search(pattern, check, re.IGNORECASE):
            return True, "helyi/régiós csatorna"

    return False, ""


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print()
    print("========================================")
    print(" MAGYAR IPTV SZŰRŐ")
    print("========================================")
    print()

    database = load_database()

    print()
    print("Magyar IPTV lista letöltése...")

    text = download(SOURCE)

    lines = text.splitlines()

    output = ["#EXTM3U"]

    total = 0
    removed = 0
    kept = 0

    seen = set()

    removed_channels = []

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

        while j < len(lines):

            candidate = lines[j].strip()

            if candidate and not candidate.startswith("#"):
                url = candidate
                break

            j += 1

        channel_id = get_attr(info, "tvg-id")
        channel_name = info.split(",", 1)[-1].strip()

        clean_id = base_id(channel_id)

        remove, reason = should_exclude(
            info,
            database
        )

        # ----------------------------------------------------
        # HIBÁS STREAM
        # ----------------------------------------------------

        if not url:
            remove = True
            reason = "nincs stream URL"

        # ----------------------------------------------------
        # DUPLIKÁCIÓ
        # ----------------------------------------------------

        key = normalize(clean_id or channel_name)

        if not key:
            remove = True
            reason = "nincs azonosító"

        elif key in seen:
            remove = True
            reason = "duplikátum"

        # ----------------------------------------------------
        # EREDMÉNY
        # ----------------------------------------------------

        if remove:

            removed += 1

            removed_channels.append(
                f"{channel_name} [{reason}]"
            )

        else:

            seen.add(key)

            output.append(info)

            # Az eredeti EXT-X/VLC sorokat is megtartjuk,
            # ha vannak az EXTINF és URL között.
            for k in range(i + 1, j):
                if lines[k].strip().startswith("#"):
                    output.append(lines[k])

            output.append(url)

            kept += 1

        i = j + 1

    # ========================================================
    # KIMENET
    # ========================================================

    OUTPUT.write_text(
        "\n".join(output) + "\n",
        encoding="utf-8"
    )

    print()
    print("========================================")
    print(" EREDMÉNY")
    print("========================================")
    print("Összes forráscsatorna:", total)
    print("Kiszűrve:", removed)
    print("Megmaradt:", kept)
    print()

    print("Kiszűrt helyi/vallási csatornák:")

    for item in removed_channels:
        print("  -", item)

    print()
    print("Kész:", OUTPUT)


if __name__ == "__main__":
    main()
