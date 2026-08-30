import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
OUTPUT = Path("magyar.m3u")

KEEP_IDS = {
    "DunaWorld.hu",
}

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
    "OrszaggyulesOGYplenaris.hu",
    "OrszaggyulesOGYTAB.hu",
    "WilliamsTV.hu",
}

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

RADIO_WORDS = (
    "rádió",
    "radio",
)


def download(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 IPTV Filter"}
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read().decode("utf-8", errors="replace")


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


def should_remove(info):
    channel_id = get_attr(info, "tvg-id")
    group = get_attr(info, "group-title")
    name = info.split(",", 1)[-1].strip()

    base_channel_id = clean_id(channel_id)

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

    if base_channel_id in EXCLUDE_IDS:
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

        while j < len(lines):
            candidate = lines[j].strip()

            if candidate and not candidate.startswith("#"):
                url = candidate
                break

            j += 1

        name = info.split(",", 1)[-1].strip()
        channel_id = get_attr(info, "tvg-id")
        base_channel_id = clean_id(channel_id)

        key = normalize(base_channel_id or name)

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

    # Ha a Duna World nem került át a countries/hu.m3u forrásból,
    # az aktuális IPTV-org streams/hu.m3u forrásból megpróbáljuk
    # külön hozzáadni.
    if not duna_world_found:
        print("Duna World nincs az országlistában, külön hozzáadás...")

        try:
            stream_text = download(
                "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hu.m3u"
            )

            stream_lines = stream_text.splitlines()

            i = 0

            while i < len(stream_lines):
                line = stream_lines[i].strip()

                if not line.startswith("#EXTINF:"):
                    i += 1
                    continue

                info = line
                channel_id = get_attr(info, "tvg-id")
                base_channel_id = clean_id(channel_id)

                if base_channel_id == "DunaWorld.hu":
                    j = i + 1
                    extra_lines = []

                    while j < len(stream_lines):
                        candidate = stream_lines[j].strip()

                        if candidate and not candidate.startswith("#"):
                            extra_lines.append(candidate)
                            break

                        j += 1

                    if extra_lines:
                        result.append(info)

                        # Megőrizzük az esetleges VLC/HTTP opciókat is.
                        k = i + 1
                        while k < j:
                            option = stream_lines[k].strip()

                            if option.startswith("#EXTVLCOPT:"):
                                result.append(option)

                            k += 1

                        result.append(extra_lines[0])

                        kept += 1
                        duna_world_found = True

                        print("KÜLÖN HOZZÁADVA: Duna World")

                    break

                i += 1

        except Exception as e:
            print("Duna World külön hozzáadása sikertelen:", e)

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    print()
    print("==============================")
    print("Forrás:", total)
    print("Kiszűrve:", excluded)
    print("Megmaradt:", kept)

    if duna_world_found:
        print("Duna World: MEGTALÁLVA ÉS MEGTARTVA")
    else:
        print("Duna World: NEM SIKERÜLT HOZZÁADNI")

    print("==============================")


if __name__ == "__main__":
    main()
