#!/usr/bin/env python3

import re
import urllib.request
from pathlib import Path
from unicodedata import normalize

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")

RELIGIOUS_WORDS = {
"vallasi",
"religious",
"christian",
"gospel",
"church",
"catholic",
"katolikus",
"reformatus",
"evangelikus",
"biblia",
"bible",
"jesus",
"jezus",
}

LOCAL_WORDS = {
"varosi",
"varos tv",
"city tv",
"citytv",
"local tv",
"localtv",
"helyi tv",
"helyitv",
"tersegi",
"terseg tv",
"regionalis",
"regionalis tv",
"regios tv",
"megyei tv",
"megye tv",
"keruleti tv",
"district tv",
"municipal",
"onkormanyzati",
}

RADIO_WORDS = {
"radio",
"radio.",
"radio fm",
"radio am",
}

def normalize_text(value):
value = value.lower()
value = normalize("NFKD", value)
value = "".join(
char for char in value
if not 0x300 <= ord(char) <= 0x36F
)
value = re.sub(r"\s+", " ", value)
return value.strip()

def download_source():
request = urllib.request.Request(
SOURCE,
headers={
"User-Agent": "Mozilla/5.0"
}
)

with urllib.request.urlopen(
    request,
    timeout=60
) as response:
    return response.read().decode(
        "utf-8",
        errors="replace"
    )

def parse_playlist(text):
channels = []
current = []

for raw_line in text.splitlines():
    line = raw_line.strip()

    if not line:
        continue

    if line.startswith("#EXTINF"):
        if current:
            channels.append(current)

        current = [line]

    elif current:
        current.append(line)

if current:
    channels.append(current)

return channels

def get_extinf(channel):
for line in channel:
if line.startswith("#EXTINF"):
return line

return ""

def get_name(channel):
line = get_extinf(channel)

if "," not in line:
    return ""

return line.split(",", 1)[1].strip()

def get_attribute(channel, attribute):
line = get_extinf(channel)

pattern = rf'{re.escape(attribute)}="([^"]*)"'
match = re.search(
    pattern,
    line,
    re.IGNORECASE
)

if match:
    return match.group(1).strip()

return ""

def get_search_text(channel):
name = get_name(channel)
group = get_attribute(channel, "group-title")
category = get_attribute(channel, "category")
country = get_attribute(channel, "tvg-country")
language = get_attribute(channel, "tvg-language")

return normalize_text(
    " ".join(
        [
            name,
            group,
            category,
            country,
            language,
        ]
    )
)

def contains_word(text, words):
for word in words:
if word in text:
return True

return False

def is_radio(channel):
text = get_search_text(channel)
name = normalize_text(get_name(channel))

if contains_word(name, RADIO_WORDS):
    return True

category = normalize_text(
    get_attribute(channel, "category")
)

if category == "radio":
    return True

if "radio" in category:
    return True

return False

def is_religious(channel):
text = get_search_text(channel)

return contains_word(
    text,
    RELIGIOUS_WORDS
)

def is_local_or_regional(channel):
name = normalize_text(get_name(channel))
group = normalize_text(
get_attribute(channel, "group-title")
)

combined = f"{name} {group}".strip()

if contains_word(
    combined,
    LOCAL_WORDS
):
    return True

return False

def is_allowed(channel):
name = get_name(channel)

if not name:
    return False

if is_radio(channel):
    return False

if is_religious(channel):
    return False

if is_local_or_regional(channel):
    return False

return True

def duplicate_key(channel):
name = normalize_text(
get_name(channel)
)

name = re.sub(
    r"\b(uhd|fhd|hd|sd|1080p|720p|576p|480p)\b",
    "",
    name
)

name = re.sub(
    r"\s+",
    " ",
    name
)

return name.strip()

def main():
print("Magyar IPTV lista frissítése...")
print(f"Forrás: {SOURCE}")

source = download_source()
channels = parse_playlist(source)

result = ["#EXTM3U"]

seen = set()

kept = 0
removed = 0
duplicates = 0

for channel in channels:
    if not is_allowed(channel):
        removed += 1
        continue

    key = duplicate_key(channel)

    if not key:
        removed += 1
        continue

    if key in seen:
        duplicates += 1
        continue

    seen.add(key)

    result.extend(channel)
    kept += 1

OUTPUT.write_text(
    "\n".join(result) + "\n",
    encoding="utf-8"
)

print("")
print("===== EREDMÉNY =====")
print(f"Forrás:     {len(channels)}")
print(f"Megmaradt:  {kept}")
print(f"Kiszűrve:   {removed}")
print(f"Duplikátum: {duplicates}")
print(f"Kimenet:    {OUTPUT}")
print("====================")

if name == "main":
main()
