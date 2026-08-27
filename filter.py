import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
OUTPUT = Path("magyar.m3u")

# Egyértelműen kizárt témák és helyi TV megnevezések.
EXCLUDE = [
    "radio",
    "rádió",
    "religious",
    "vallási",
    "christian",
    "gospel",
    "catholic",
    "katolikus",
    "református",
    "reformatus",
    "evangélikus",
    "evangelikus",
    "biblia",
    "bible",
    "helyi tv",
    "helyi televízió",
    "helyi televizio",
    "városi tv",
    "varosi tv",
    "városi televízió",
    "varosi televizio",
    "regionális tv",
    "regionalis tv",
    "régiós tv",
    "regios tv",
    "térségi tv",
    "tersegi tv",
    "megyei tv",
    "megye tv",
    "kerületi tv",
    "keruleti tv",
    "önkormányzati tv",
    "onkormanyzati tv",
    "local tv",
    "localtv",
    "city tv",
    "citytv",
    "municipal tv",
    "community tv",
    "országgyűlés",
    "orszaggyules",
    "ogy plenáris",
    "ogy plenaris",
    "ogy tab"
]


def normalize(text):
    text = str(text or "").lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ö": "o",
        "ő": "o",
        "ú": "u",
        "ü": "u",
        "ű": "u"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return re.sub(r"\s+", " ", text).strip()


def main():

    print("Magyar IPTV lista letöltése...")

    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        data = response.read().decode(
            "utf-8",
            "replace"
        )

    blocks = re.split(
        r"(?=#EXTINF)",
        data
    )

    result = []
    seen = set()

    for block in blocks:

        block = block.strip()

        if not block.startswith("#EXTINF"):
            continue

        lines = block.splitlines()

        if not lines:
            continue

        extinf = lines[0]

        if "," not in extinf:
            continue

        name = extinf.split(
            ",",
            1
        )[1].strip()

        search_text = normalize(
            block
        )

        excluded = False

        for word in EXCLUDE:

            if normalize(word) in search_text:
                excluded = True
                break

        if excluded:
            continue

        key = normalize(name)

        if key in seen:
            continue

        seen.add(key)
        result.append(block)

    def channel_name(block):
        line = block.splitlines()[0]

        if "," in line:
            return normalize(
                line.split(",", 1)[1]
            )

        return ""

    result.sort(
        key=channel_name
    )

    lines = [
        "#EXTM3U",
        "# Magyar nyelvű magyar TV csatornák",
        "# Vallási és helyi csatornák nélkül"
    ]

    lines.extend(result)

    OUTPUT.write_text(
        "\n\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print(
        "Forrás csatornák:",
        len(blocks)
    )

    print(
        "Megmaradt csatornák:",
        len(result)
    )

    print(
        "magyar.m3u elkészült."
    )


if __name__ == "__main__":
    main()
