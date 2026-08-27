```python
#!/usr/bin/env python3

import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")


# ============================================================
# CSAK EZEK A CSATORNÁK KERÜLHETNEK A LISTÁBA
# ============================================================

ALLOWED = {
    # MTVA
    "m1",
    "m2",
    "m4 sport",
    "m5",
    "duna",
    "duna world",

    # Országos kereskedelmi / közéleti
    "rtl",
    "tv2",
    "atv",
    "atv spirit",

    # Magyar film / szórakoztató
    "film+",
    "film cafe",
    "film4",
    "filmbox+ comedy magyar",
    "filmbox+ emotion hungary",
    "filmbox+ one magyar",
    "magyar mozi tv",
    "mozi+",
    "moziverzum",
    "moziklub",
    "izaura tv",
    "jocky tv",
    "life tv",
    "fem3",
    "fix tv",
    "galaxy4",
    "hatoscsatorna",
    "muzsika tv",

    # Gyerek
    "minimax",
    "disney channel",
    "nickelodeon",
    "nick jr.",
    "nicktoons",
    "jimjam",
    "kölyökklub",

    # Ismeretterjesztő
    "history",
    "national geographic",
    "national geographic wild",
    "love nature",

    # Zene
    "h!t music channel",

    # Hírek
    "euronews hungarian",

    # Egyéb országos
    "spektrum",
    "spektrum home",
    "viasat3",
    "viasat6",
    "cool",
    "rtl gold",
    "rtl klub",
}


def normalize(name):
    return (
        name.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ö", "o")
        .replace("ő", "o")
        .replace("ú", "u")
        .replace("ü", "u")
        .replace("ű", "u")
        .strip()
    )


def download_playlist():
    request = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


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
        if line.startswith("#EXTINF") and "," in line:
            return line.split(",", 1)[1].strip()

    return ""


def is_allowed(name):
    n = normalize(name)

    # Pontos egyezés
    if n in {normalize(x) for x in ALLOWED}:
        return True

    # Minőségi jelölések eltávolítása
    clean = n

    for marker in [
        " (1080p)",
        " (720p)",
        " (576p)",
        " (480p)",
        " (416p)",
        " (360p)",
        " [not 24/7]",
    ]:
        clean = clean.replace(marker, "")

    clean = clean.strip()

    if clean in {normalize(x) for x in ALLOWED}:
        return True

    return False


def main():
    print("Magyar IPTV lista letöltése...")

    source = download_playlist()
    channels = get_channels(source)

    print("Forrás csatornái:", len(channels))

    result = ["#EXTM3U"]

    kept = 0
    removed = 0

    for channel in channels:
        name = get_name(channel)

        if is_allowed(name):
            result.extend(channel)
            kept += 1
        else:
            removed += 1

    OUTPUT.write_text(
        "\n".join(result) + "\n",
        encoding="utf-8"
    )

    print("")
    print("================================")
    print(" MAGYAR IPTV LISTA")
    print("================================")
    print("Forrás:", len(channels))
    print("Benne maradt:", kept)
    print("Kiszűrve:", removed)
    print("Fájl:", OUTPUT)
    print("================================")


if __name__ == "__main__":
    main()
```
