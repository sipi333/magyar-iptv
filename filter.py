import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
OUTPUT = Path("magyar.m3u")


# ============================================================
# HELYI / VÁROSI / KERÜLETI / RÉGIÓS CSATORNÁK
# ============================================================

EXCLUDE_NAMES = [
    "16tv Budapest",
    "Alföld TV",
    "Bábolnai TV",
    "Bajai TV",
    "Balaton TV",
    "Berente TV",
    "Budapest Európa Televízió",
    "City TV",
    "Csurgó TV",
    "Daru TV",
    "DTV",
    "Első Kerület TV",
    "ESTV",
    "Fehérvár TV",
    "Globo TV",
    "Gólya TV",
    "Gyöngyösi TV",
    "Hangulat TV",
    "Hatcsatorna",
    "Hegyvidék TV",
    "Hévízi TV",
    "Jász... Térségi TV",
    "Kanizsa TV",
    "Kapos TV",
    "Karcag TV",
    "Kecskeméti TV",
    "Kiskőrös TV",
    "Komáromi Televízió",
    "Komlós TV",
    "Liceum TV",
    "Makói Városi TV",
    "Mezőkövesdi Televízió",
    "Móra-Net TV",
    "Ózdi Városi TV",
    "PilisTV",
    "Putnok Városi TV",
    "Rákosmente TV",
    "Régió TV",
    "RégióPlusz TV",
    "Soltvadkerti Televízió",
    "Szécsényi TV",
    "Szolnok TV",
    "Tatai TV",
    "TelePaks",
    "Tisza TV",
    "TriMedio TV",
    "TV7 Békéscsaba",
    "TV Budakalász",
    "TV Eger",
    "TV Keszthely",
    "TV Szentendre",
    "TV Vásárhelyi Televízió",
    "Völgyhíd TV",
    "VTV Füzesabony",
    "VTV Mór",
    "XV TV",
    "Zalaegerszegi TV",
    "Zugló TV",
]


# ============================================================
# HELYI / REGIONÁLIS NÉVMINTÁK
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

    r"\bmegyei\s+tv\b",
    r"\bmegyei\s+televízió\b",
    r"\bmegyei\s+televizio\b",

    r"\bkerületi\s+tv\b",
    r"\bkeruleti\s+tv\b",

    r"\bönkormányzati\s+tv\b",
    r"\bonkormanyzati\s+tv\b",

    r"\bközösségi\s+tv\b",
    r"\bkozossegi\s+tv\b",
]


# ============================================================
# VALLÁSI CSATORNÁK
# ============================================================

RELIGIOUS = [
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
]


# ============================================================
# RÁDIÓK IS KERÜLJENEK KI
# ============================================================

RADIO = [
    "rádió",
    "radio",
]


def download(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
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

    text = (
        text
        .replace("ő", "ö")
        .replace("ű", "ü")
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_attr(line, attribute):
    match = re.search(
        rf'{re.escape(attribute)}="([^"]*)"',
        line
    )

    if match:
        return match.group(1)

    return ""


def remove_quality_suffix(channel_id):
    """
    Például:

    16tvBudapest.hu@SD
    16tvBudapest.hu@HD

    ->

    16tvBudapest.hu
    """

    return channel_id.split(
        "@",
        1
    )[0]


def should_remove(info):

    name = info.split(
        ",",
        1
    )[-1].strip()

    tvg_id = get_attr(
        info,
        "tvg-id"
    )

    group = get_attr(
        info,
        "group-title"
    )

    text = normalize(
        name
        + " "
        + tvg_id
        + " "
        + group
    )

    # --------------------------------------------------------
    # NÉV ALAPÚ FIX KIZÁRÁS
    # --------------------------------------------------------

    for excluded in EXCLUDE_NAMES:

        if normalize(excluded) in text:
            return True

    # --------------------------------------------------------
    # TVG-ID @SD / @HD LEVÁGÁSA
    # --------------------------------------------------------

    clean_id = normalize(
        remove_quality_suffix(tvg_id)
    )

    for excluded in EXCLUDE_NAMES:

        excluded_clean = normalize(
            excluded
        )

        if (
            excluded_clean
            and excluded_clean.replace(" ", "")
            in clean_id.replace(" ", "")
        ):
            return True

    # --------------------------------------------------------
    # HELYI / REGIONÁLIS
    # --------------------------------------------------------

    for pattern in LOCAL_PATTERNS:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):
            return True

    # --------------------------------------------------------
    # VALLÁSI
    # --------------------------------------------------------

    for word in RELIGIOUS:

        if word in text:
            return True

    # --------------------------------------------------------
    # RÁDIÓ
    # --------------------------------------------------------

    for word in RADIO:

        if word in text:
            return True

    return False


def main():

    print(
        "IPTV-org magyar lista letöltése..."
    )

    text = download(
        SOURCE
    )

    lines = text.splitlines()

    output = [
        "#EXTM3U"
    ]

    total = 0
    removed = 0
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

        j = i + 1

        while j < len(lines):

            candidate = lines[j].strip()

            if (
                candidate
                and not candidate.startswith("#")
            ):
                url = candidate
                break

            j += 1

        name = info.split(
            ",",
            1
        )[-1].strip()

        tvg_id = get_attr(
            info,
            "tvg-id"
        )

        clean_id = remove_quality_suffix(
            tvg_id
        )

        key = normalize(
            clean_id or name
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

            removed += 1

            print(
                "KISZŰRVE:",
                name
            )

        else:

            seen.add(key)

            output.append(info)
            output.append(url)

            kept += 1

        i = j + 1

    OUTPUT.write_text(
        "\n".join(output)
        + "\n",
        encoding="utf-8"
    )

    print()
    print("==============================")
    print(
        "Forrás:",
        total
    )
    print(
        "Kiszűrve:",
        removed
    )
    print(
        "Megmaradt:",
        kept
    )
    print("==============================")


if __name__ == "__main__":
    main()
