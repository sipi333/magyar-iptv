import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
OUTPUT = Path("magyar.m3u")

BAD = [
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
    "jesus",
    "jézus",
    "jezus",
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
    "community tv"
]


def norm(text):
    text = str(text or "").lower()
    text = text.replace("á", "a")
    text = text.replace("é", "e")
    text = text.replace("í", "i")
    text = text.replace("ó", "o")
    text = text.replace("ö", "o")
    text = text.replace("ő", "o")
    text = text.replace("ú", "u")
    text = text.replace("ü", "u")
    text = text.replace("ű", "u")
    return re.sub(r"\s+", " ", text).strip()


def main():

    print("IPTV-org magyar lista letöltése...")

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

    blocks = [
        block.strip()
        for block in blocks
        if block.strip().startswith("#EXTINF")
    ]

    print(
        "Forrás csatornák:",
        len(blocks)
    )

    result = []
    seen = set()

    for block in blocks:

        lines = block.splitlines()

        if not lines:
            continue

        name = ""

        for line in lines:

            if line.startswith("#EXTINF"):

                if "," in line:
                    name = line.split(
                        ",",
                        1
                    )[1].strip()

                break

        if not name:
            continue

        text = norm(block)

        excluded = False

        for bad in BAD:

            if norm(bad) in text:
                excluded = True
                break

        if excluded:
            continue

        key = norm(name)

        if key in seen:
            continue

        seen.add(key)

        result.append(block)

    result.sort(
        key=lambda block: norm(
            block.split(",", 1)[-1]
            .splitlines()[0]
        )
    )

    output = [
        "#EXTM3U"
    ]

    output.extend(result)

    OUTPUT.write_text(
        "\n".join(output) + "\n",
        encoding="utf-8"
    )

    print(
        "Megmaradt csatornák:",
        len(result)
    )

    print(
        "Playlist elkészült:",
        OUTPUT
    )


if __name__ == "__main__":
    main()
