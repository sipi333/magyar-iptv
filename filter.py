import re
import urllib.request
from pathlib import Path


SOURCE = "https://iptv-org.github.io/iptv/streams/hu.m3u"
OUTPUT = Path("magyar.m3u")


# Ezeket biztosan kizárjuk.
EXCLUDE = [
    # rádió
    "radio",
    "rádió",

    # vallási
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
    "apostol",

    # helyi / regionális
    "városi tv",
    "varosi tv",
    "városi televízió",
    "varosi televizio",
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
    "helyi tv",
    "helyi televízió",
    "helyi televizio",
    "megyei tv",
    "megyei televízió",
    "megyei televizio",
    "kerületi tv",
    "keruleti tv",
    "kerületi televízió",
    "keruleti televizio",
    "district tv",
    "municipal",
    "önkormányzati",
    "onkormanyzati",
    "city tv",
    "citytv",
    "local tv",
    "localtv",

    # tipikus helyi adó elnevezések
    "vtv ",
    "tv budakalász",
    "tv budakalasz",
]


def normalize(text):
    text = text.lower()
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


def get_channel_name(block):
    for line in block.splitlines():

        if line.startswith("#EXTINF"):

            if "," in line:
                return line.split(",", 1)[1].strip()

    return ""


def is_excluded(block):

    name = normalize(
        get_channel_name(block)
    )

    whole = normalize(block)

    for word in EXCLUDE:

        if normalize(word) in name:
            return True

        if normalize(word) in whole:
            return True

    return False


def main():

    print("IPTV-org magyar streamlista letöltése...")

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

    # Egy EXTINF blokk = egy csatorna
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
        f"Forrásban található bejegyzések: {len(blocks)}"
    )

    result = []
    seen = set()

    for block in blocks:

        if is_excluded(block):
            continue

        name = normalize(
            get_channel_name(block)
        )

        if not name:
            continue

        # Duplikált csatornák kiszűrése
        if name in seen:
            continue

        seen.add(name)
        result.append(block)

    # ABC sorrend
    result.sort(
        key=lambda x: normalize(
            get_channel_name(x)
        )
    )

    output = [
        "#EXTM3U",
        "# Magyar nyelvű magyarországi TV csatornák",
        "# Vallási, rádió, helyi és regionális csatornák kizárva",
        "# Automatikusan generálva az iptv-org listából",
        ""
    ]

    output.extend(result)

    OUTPUT.write_text(
        "\n\n".join(output) + "\n",
        encoding="utf-8"
    )

    print(
        f"Megmaradt csatornák: {len(result)}"
    )

    print(
        f"Elkészült: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
