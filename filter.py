import csv
import io
import re
import urllib.request
from pathlib import Path

# ============================================================
# FORRÁSOK
# ============================================================

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
DATABASE = "https://raw.githubusercontent.com/iptv-org/database/master/data/channels.csv"

OUTPUT = Path("magyar.m3u")

# ============================================================
# FIXEN KIZÁRANDÓ CSATORNÁK
# ============================================================

EXCLUDE_IDS = {
    # A képeken szereplő helyi / városi / regionális csatornák
    "BTV.hu",
    "BajaiTV.hu",
    "BalatonTV.hu",
    "BerenteTV.hu",
    "CsurgoTV.hu",
    "DaruTV.hu",
    "DTV.hu",
    "EgykerTV.hu",
    "ESTV.hu",
    "FehervarTV.hu",
    "16tvBudapest.hu",
    "BudapestEuropaTelevizio.hu",

    # Vallási
    "ApostolTV.hu",
    "PaxTV.hu",
    "EWTN.hu",
    "BonumTV.hu",
}

# ============================================================
# HELYI / VÁROSI / RÉGIÓS KULCSSZAVAK
# ============================================================

LOCAL_WORDS = (
    "városi tv",
    "varosi tv",
    "városi televízió",
    "varosi televizio",
    "városi televizio",

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
    "megye tv",
    "megyei televízió",
    "megye televízió",

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
# VALLÁSI KULCSSZAVAK
# ============================================================

RELIGIOUS_WORDS = (
    "apostol",
    "pax tv",
    "paxtv",
    "ewtn",
    "bonum",

    "katolikus",
    "katolikus tv",
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
# RÁDIÓ KIZÁRÁSA
# ============================================================

RADIO_WORDS = (
    "rádió",
    "radio",
)

# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def download(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 IPTV Filter"
        },
    )

    with urllib.request.urlopen(req, timeout=180) as response:
        return response.read().decode("utf-8", errors="replace")


def get_attr(line, name):
    match = re.search(
        rf'(?:^|\s){re.escape(name)}="([^"]*)"',
        line
    )
    return match.group(1) if match else ""


def norm(text):
    text = str(text or "").lower()

    # ékezetek megtartása, de whitespace egységesítése
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def compact(text):
    """
    Összehúzott név összehasonlításhoz.
    Például:
    'Zugló TV' -> 'zuglotv'
    """
    return re.sub(r"[^a-z0-9áéíóöőúüű]", "", norm(text))


# ============================================================
# IPTV-ORG ADATBÁZIS BETÖLTÉSE
# ============================================================

def load_database():
    print("IPTV-org csatorna-adatbázis letöltése...")

    text = download(DATABASE)

    rows = {}

    reader = csv.DictReader(io.StringIO(text))

    for row in reader:
        channel_id = row.get("id", "").strip()

        if channel_id:
            rows[channel_id] = row

    print("Adatbázisban talált csatornák:", len(rows))

    return rows


# ============================================================
# HELYI / VALLÁSI ELLENŐRZÉS
# ============================================================

def is_excluded(info, database):
    channel_id = get_attr(info, "tvg-id")
    name = info.split(",", 1)[-1].strip()

    group = get_attr(info, "group-title")

    db = database.get(channel_id, {})

    db_name = db.get("name", "")
    db_category = db.get("category", "")
    db_country = db.get("country", "")
    db_subdivision = db.get("subdivision", "")
    db_city = db.get("city", "")

    # Mindent egyetlen ellenőrzési szövegbe teszünk
    check = norm(
        " ".join(
            [
                channel_id,
                name,
                group,
                db_name,
                db_category,
                db_country,
                db_subdivision,
                db_city,
            ]
        )
    )

    compact_check = compact(check)

    # --------------------------------------------------------
    # 1. FIX ID
    # --------------------------------------------------------

    if channel_id in EXCLUDE_IDS:
        return True, "fix kizárási lista"

    # --------------------------------------------------------
    # 2. VALLÁSI KATEGÓRIA
    # --------------------------------------------------------

    category = norm(db_category)

    if category == "religious":
        return True, "IPTV-org Religious kategória"

    if "religious" in category:
        return True, "vallási kategória"

    # --------------------------------------------------------
    # 3. VALLÁSI NÉV / METAADAT
    # --------------------------------------------------------

    for word in RELIGIOUS_WORDS:
        if word in check:
            return True, f"vallási kulcsszó: {word}"

    # --------------------------------------------------------
    # 4. HELYI / VÁROSI / RÉGIÓS
    # --------------------------------------------------------

    for word in LOCAL_WORDS:
        if word in check:
            return True, f"helyi kulcsszó: {word}"

    # --------------------------------------------------------
    # 5. RÁDIÓ
    # --------------------------------------------------------

    for word in RADIO_WORDS:
        if word in check:
            return True, f"rádió: {word}"

    # --------------------------------------------------------
    # 6. KIFEJEZETTEN HELYI TV-NÉV MINTÁK
    # --------------------------------------------------------

    local_patterns = (
        r"\btv\s+budakalász\b",
        r"\btv\s+eger\b",
        r"\btv\s+keszthely\b",
        r"\btv\s+szentendre\b",
        r"\btv\s+vásárhely\b",
        r"\btv\s+vasarhely\b",
        r"\bzugló\s+tv\b",
        r"\bzuglo\s+tv\b",
        r"\brákosmente\s+tv\b",
        r"\brakosmente\s+tv\b",
        r"\btelepaks\b",
        r"\btisza\s+tv\b",
        r"\bszolnok\s+tv\b",
        r"\bkecskeméti\s+tv\b",
        r"\bkecskemeti\s+tv\b",
        r"\bkapos\s+tv\b",
        r"\bkanizsa\s+tv\b",
        r"\bfehérvár\s+tv\b",
        r"\bfehervar\s+tv\b",
        r"\bgyöngyösi\s+tv\b",
        r"\bgyongyosi\s+tv\b",
        r"\bbábolnai\s+tv\b",
        r"\b bábolna\s+tv\b",
        r"\bbajai\s+tv\b",
        r"\bbalaton\s+tv\b",
        r"\bberente\s+tv\b",
        r"\bcsurgó\s+tv\b",
        r"\bcsurgo\s+tv\b",
        r"\bkarcag\s+tv\b",
        r"\bkiskőrös\s+tv\b",
        r"\bkiskoros\s+tv\b",
        r"\bkomáromi\s+televízió\b",
        r"\bkomaromi\s+televizio\b",
        r"\bmakói\s+városi\s+tv\b",
        r"\bmakoi\s+varosi\s+tv\b",
        r"\bmezőkövesdi\s+televízió\b",
        r"\bmezokovesdi\s+televizio\b",
        r"\bózdi\s+városi\s+tv\b",
        r"\bozdi\s+varosi\s+tv\b",
        r"\bputnok\s+városi\s+tv\b",
        r"\bputnok\s+varosi\s+tv\b",
        r"\bszécsényi\s+tv\b",
        r"\bszecsenyi\s+tv\b",
        r"\btatai\s+tv\b",
        r"\bvölgyhíd\s+tv\b",
        r"\bvolgyhid\s+tv\b",
        r"\bvtv\s+füzesabony\b",
        r"\bvtv\s+fuzesabony\b",
        r"\bvtv\s+mór\b",
        r"\bvtv\s+mor\b",
        r"\bzalaegerszegi\s+tv\b",
        r"\bxv\s+tv\b",
    )

    for pattern in local_patterns:
        if re.search(pattern, check, re.IGNORECASE):
            return True, f"helyi TV minta: {pattern}"

    # --------------------------------------------------------
    # NEM KIZÁRANDÓ
    # --------------------------------------------------------

    return False, ""


# ============================================================
# FŐPROGRAM
# ============================================================

def main():

    print("==========================================")
    print(" MAGYAR IPTV AUTOMATIKUS SZŰRŐ")
    print("==========================================")

    database = load_database()

    print()
    print("IPTV-org magyar playlist letöltése...")

    text = download(SOURCE)

    lines = text.splitlines()

    result = ["#EXTM3U"]

    total = 0
    kept = 0
    excluded = 0

    excluded_reasons = {}

    seen = set()

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

        name = info.split(",", 1)[-1].strip()

        key = norm(channel_id or name)

        remove, reason = is_excluded(info, database)

        # ----------------------------------------------------
        # DUPLIKÁCIÓ
        # ----------------------------------------------------

        if not url:
            remove = True
            reason = "nincs stream URL"

        elif not key:
            remove = True
            reason = "nincs csatornaazonosító"

        elif key in seen:
            remove = True
            reason = "duplikátum"

        # ----------------------------------------------------
        # EREDMÉNY
        # ----------------------------------------------------

        if remove:

            excluded += 1

            excluded_reasons[reason] = (
                excluded_reasons.get(reason, 0) + 1
            )

        else:

            seen.add(key)

            result.append(info)
            result.append(url)

            kept += 1

        i = j + 1

    # ========================================================
    # FÁJL ÍRÁSA
    # ========================================================

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    print()
    print("==========================================")
    print(" EREDMÉNY")
    print("==========================================")
    print("Forrásból talált:", total)
    print("Kizárt:", excluded)
    print("Megmaradt:", kept)
    print("Kimeneti fájl:", OUTPUT)
    print()

    print("Kizárások oka szerint:")

    for reason, count in sorted(
        excluded_reasons.items(),
        key=lambda x: (-x[1], x[0])
    ):
        print(f"  {count:4} - {reason}")

    print()
    print("magyar.m3u elkészült.")


if __name__ == "__main__":
    main()
