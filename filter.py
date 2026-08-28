import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
OUTPUT = Path("magyar.m3u")

# Egyértelműen helyi / városi / regionális csatornaazonosítók
EXCLUDE_IDS = {
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
}

LOCAL_WORDS = (
    "városi tv", "varosi tv",
    "városi televízió", "varosi televizio",
    "helyi tv", "helyi televízió", "helyi televizio",
    "regionális tv", "regionalis tv",
    "régiós tv", "regios tv",
    "térségi tv", "tersegi tv",
    "megyei tv", "megye tv",
    "kerületi tv", "keruleti tv",
    "önkormányzati tv", "onkormanyzati tv",
    "közösségi tv", "kozossegi tv",
    "local tv", "localtv",
    "city tv", "citytv",
)

RELIGIOUS_WORDS = (
    "ewtn", "apostol tv", "apostol",
    "bonum", "katolikus", "catholic",
    "református", "reformatus",
    "evangélikus", "evangelikus",
    "keresztény", "kereszteny",
    "christian", "gospel", "church",
    "biblia", "bible",
)

RADIO_WORDS = (
    "rádió", "radio",
)

def download(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
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
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def main():
    print("iptv-org magyar lista letöltése...")
    text = download(SOURCE)

    lines = text.splitlines()
    result = ["#EXTM3U"]

    total = 0
    kept = 0
    excluded = 0
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

        check = norm(
            channel_id + " " + name + " " +
            get_attr(info, "group-title")
        )

        remove = False

        if channel_id in EXCLUDE_IDS:
            remove = True

        if any(word in check for word in LOCAL_WORDS):
            remove = True

        if any(word in check for word in RELIGIOUS_WORDS):
            remove = True

        if any(word in check for word in RADIO_WORDS):
            remove = True

        # Ugyanazt a csatornát csak egyszer tesszük a listába.
        key = norm(channel_id or name)

        if not url or not key or key in seen:
            remove = True

        if remove:
            excluded += 1
        else:
            seen.add(key)
            result.append(info)
            result.append(url)
            kept += 1

        i = j + 1

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    print("Forrásból talált csatornák:", total)
    print("Kizárt csatornák:", excluded)
    print("Megmaradt csatornák:", kept)
    print("magyar.m3u elkészült.")


if __name__ == "__main__":
    main()
