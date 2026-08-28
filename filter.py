import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
OUTPUT = Path("magyar.m3u")

EXCLUDE = [
    "radio",
    "rádió",
    "religious",
    "vallási",
    "vallas",
    "christian",
    "gospel",
    "church",
    "catholic",
    "katolikus",
    "reformatus",
    "református",
    "evangelikus",
    "evangélikus",
    "biblia",
    "bible",
    "jesus",
    "jézus",
    "jezus",
    "városi",
    "varosi",
    "city tv",
    "citytv",
    "local tv",
    "localtv",
    "helyi tv",
    "helyitv",
    "térségi",
    "tersegi",
    "regionális",
    "regionalis",
    "régiós",
    "regios",
    "megyei",
    "megye tv",
    "kerületi",
    "keruleti",
    "district tv",
    "municipal",
    "onkormanyzati",
    "önkormányzati",
]

def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()

def main():
    request = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        data = response.read().decode(
            "utf-8",
            errors="replace"
        )

    blocks = re.split(
        r"(?=#EXTINF)",
        data
    )

    blocks = [
        block.strip()
        for block in blocks
        if block.strip().startswith("#EXTINF")
    ]

    kept = []
    seen = set()

    for block in blocks:
        text = normalize(block)

        if any(word in text for word in EXCLUDE):
            continue

        lines = block.splitlines()

        if not lines:
            continue

        name = lines[0].split(",", 1)[-1].strip()

        key = normalize(name)

        if not key or key in seen:
            continue

        seen.add(key)
        kept.append(block)

    OUTPUT.write_text(
        "#EXTM3U\n" +
        "\n".join(kept) +
        "\n",
        encoding="utf-8"
    )

    print("Forrás csatornák:", len(blocks))
    print("Megmaradt csatornák:", len(kept))
    print("Kimenet:", OUTPUT)

if __name__ == "__main__":
    main()
