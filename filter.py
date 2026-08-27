#!/usr/bin/env python3

import re
import urllib.request
from pathlib import Path
from unicodedata import normalize as unicode_normalize

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")

EXCLUDED_WORDS = [
"vallási",
"vallas",
"vallás",
"religious",
"christian",
"gospel",
"church",
"catholic",
"katolikus",
"református",
"reformatus",
"evangélikus",
"evangelikus",
"biblia",
"bible",
"jesus",
"jézus",
"jezus",
"rádió",
"radio",
]

LOCAL_WORDS = [
"városi",
"varosi",
"térségi",
"tersegi",
"regionális",
"regionalis",
"régiós",
"regios",
"megyei",
"kerületi",
"keruleti",
"helyi",
"térség",
"terseg",
"város",
"varos",
"city tv",
"citytv",
"local tv",
"localtv",
"district tv",
"municipal",
]

def normalize_text(value):
value = value.lower().strip()
value = unicode_normalize("NFKD", value)
value = "".join(
char for char in value
if not 0x300 <= ord(char) <= 0x36F
)
value = re.sub(r"\s+", " ", value)
return value

EXCLUDED = tuple(normalize_text(x) for x in EXCLUDED_WORDS)
LOCAL = tuple(normalize_text(x) for x in LOCAL_WORDS)

def download_source():
request = urllib.request.Request(
SOURCE,
headers={"User-Agent": "Mozilla/5.0"}
)

```
with urllib.request.urlopen(request, timeout=60) as response:
    return response.read().decode(
        "utf-8",
        errors="replace"
    )
```

def parse_channels(text):
channels = []
current = []

```
for line in text.splitlines():
    line = line.strip()

    if line.startswith("#EXTINF"):
        if current:
            channels.append(current)

        current = [line]

    elif current:
        current.append(line)

if current:
    channels.append(current)

return channels
```

def extinf(channel):
for line in channel:
if line.startswith("#EXTINF"):
return line

```
return ""
```

def channel_name(channel):
line = extinf(channel)

```
if "," not in line:
    return ""

return line.split(",", 1)[1].strip()
```

def attribute(channel, name):
line = extinf(channel)

```
match = re.search(
    rf'{re.escape(name)}="([^"]*)"',
    line,
    re.IGNORECASE
)

if match:
    return match.group(1).strip()

return ""
```

def channel_text(channel):
name = channel_name(channel)
group = attribute(channel, "group-title")
category = attribute(channel, "category")

```
return normalize_text(
    f"{name} {group} {category}"
)
```

def is_excluded(channel):
text = channel_text(channel)

```
for word in EXCLUDED:
    if word in text:
        return True

for word in LOCAL:
    if word in text:
        return True

return False
```

def duplicate_key(channel):
name = normalize_text(channel_name(channel))

```
name = re.sub(
    r"\b(uhd|fhd|hd|sd|1080p|720p|576p|480p)\b",
    "",
    name
)

return re.sub(r"\s+", " ", name).strip()
```

def main():
print("Magyar IPTV forrás letöltése...")
print(SOURCE)

```
source = download_source()
channels = parse_channels(source)

print(f"Forrás csatornák: {len(channels)}")

output = ["#EXTM3U"]
seen = set()

kept = 0
excluded = 0
duplicates = 0

for channel in channels:
    name = channel_name(channel)

    if not name:
        excluded += 1
        continue

    if is_excluded(channel):
        excluded += 1
        continue

    key = duplicate_key(channel)

    if not key:
        excluded += 1
        continue

    if key in seen:
        duplicates += 1
        continue

    seen.add(key)
    output.extend(channel)
    kept += 1

OUTPUT.write_text(
    "\n".join(output) + "\n",
    encoding="utf-8"
)

print("")
print("===== EREDMÉNY =====")
print(f"Forrás:       {len(channels)}")
print(f"Megmaradt:    {kept}")
print(f"Kiszűrve:     {excluded}")
print(f"Duplikátum:   {duplicates}")
print(f"Kimenet:      {OUTPUT}")
print("====================")
```

if **name** == "**main**":
main()
