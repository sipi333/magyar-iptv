#!/usr/bin/env python3
import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUT = Path("magyar.m3u")

# Ezeket a névben/csoportban szereplő kifejezéseket kizárjuk.
EXCLUDE = [
    "vallás", "relig", "christ", "christian", "church", "gospel",
    "katol", "reformát", "reformatus", "evangé", "evangel",
    "istentisztelet", "biblia", "duna world radio",
    "radio", "rádió",
    "city", "városi", "varosi", "local", "region", "regional",
    "megye", "county", "municipal", "közösségi", "community",
]

# Kifejezetten regionális/városi magyar csatornák tipikus jelölései.
REGIONAL_HINTS = [
    "nyíregyháza", "nyiregyhaza", "debrecen", "miskolc", "szeged",
    "pécs", "pecs", "győr", "gyor", "szolnok", "kecskemét", "kecskemet",
    "békéscsaba", "bekescsaba", "sopron", "euro tv", "hírös", "hiros",
    "városi tv", "varosi tv", "tv plusz", "city tv",
]

def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

def excluded(block):
    low = block.lower()
    if any(x in low for x in EXCLUDE):
        return True
    if any(x in low for x in REGIONAL_HINTS):
        return True
    # Kifejezetten helyi/regionális group-title-ek.
    if re.search(r'group-title="[^"]*(local|regional|region|city|város|megye)[^"]*"', low):
        return True
    return False

src = download(SOURCE)
lines = src.splitlines()
out = ["#EXTM3U"]
current = []

for line in lines:
    if line.startswith("#EXTINF"):
        if current and not excluded("\n".join(current)):
            out.extend(current)
        current = [line]
    elif current:
        current.append(line)

if current and not excluded("\n".join(current)):
    out.extend(current)

# Duplikált EXTINF+URL párok eltávolítása.
dedup = []
seen = set()
i = 0
while i < len(out):
    if out[i].startswith("#EXTINF"):
        url = out[i+1] if i+1 < len(out) else ""
        key = (out[i], url)
        if key not in seen:
            seen.add(key)
            dedup.extend([out[i], url])
        i += 2
    else:
        i += 1

OUT.write_text("\n".join(dedup) + "\n", encoding="utf-8")
print(f"Generated {OUT} with {(len(dedup)-1)//2} channels")
