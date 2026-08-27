import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")

EXCLUDED = [
"rádió", "radio",
"vallási", "vallas", "religious",
"christian", "gospel", "church",
"catholic", "katolikus",
"református", "reformatus",
"evangélikus", "evangelikus",
"biblia", "bible", "jesus", "jézus", "jezus",
"városi", "varosi",
"térségi", "tersegi",
"regionális", "regionalis",
"régiós", "regios",
"megyei", "megye",
"kerületi", "keruleti",
"helyi tv", "helyitv",
"city tv", "citytv",
"local tv", "localtv",
"district tv",
"municipal",
"önkormányzati", "onkormanyzati"
]

def norm(text):
text = text.lower()
replacements = {
"á": "a", "é": "e", "í": "i",
"ó": "o", "ö": "o", "ő": "o",
"ú": "u", "ü": "u", "ű": "u"
}
for a, b in replacements.items():
text = text.replace(a, b)
return re.sub(r"\s+", " ", text).strip()

def excluded(text):
text = norm(text)
for word in EXCLUDED:
if norm(word) in text:
return True
return False

def main():
request = urllib.request.Request(
SOURCE,
headers={"User-Agent": "Mozilla/5.0"}
)

```
with urllib.request.urlopen(request, timeout=60) as response:
    data = response.read().decode("utf-8", errors="replace")

lines = data.splitlines()
output = ["#EXTM3U"]
seen = set()
total = 0
kept = 0
removed = 0
duplicates = 0
current = []

for line in lines:
    line = line.strip()

    if line.startswith("#EXTINF"):
        if current:
            name = current[0].split(",", 1)[-1].strip()
            key = norm(name)

            if excluded(" ".join(current)):
                removed += 1
            elif key in seen:
                duplicates += 1
            else:
                seen.add(key)
                output.extend(current)
                kept += 1

            total += 1

        current = [line]

    elif current:
        current.append(line)

if current:
    name = current[0].split(",", 1)[-1].strip()
    key = norm(name)

    if excluded(" ".join(current)):
        removed += 1
    elif key in seen:
        duplicates += 1
    else:
        output.extend(current)
        kept += 1

    total += 1

OUTPUT.write_text(
    "\n".join(output) + "\n",
    encoding="utf-8"
)

print("===== MAGYAR IPTV =====")
print("Forrás:", SOURCE)
print("Összes:", total)
print("Megmaradt:", kept)
print("Kiszűrve:", removed)
print("Duplikátum:", duplicates)
print("Kimenet:", OUTPUT)
print("========================")
```

if **name** == "**main**":
main()
