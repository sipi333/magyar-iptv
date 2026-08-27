import re
import urllib.request
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/countries/hu.m3u"
OUTPUT = Path("magyar.m3u")

# Csak ezekből a csatornákból készülhet a lista.
# Így a helyi és városi TV-k automatikusan kimaradnak.

ALLOWED = {
    "ATV.hu",
    "ATVSpirit.hu",
    "DikhTV.hu",
    "DisneyChannel.hu",
    "Duna.hu",
    "FEM3.hu",
    "FilmCafe.hu",
    "FilmPlus.hu",
    "Film4.hu",
    "FIXTV.hu",
    "Galaxy4.hu",
    "Hatoscsatorna.hu",
    "History.hu",
    "IzauraTV.hu",
    "JimJam.hu",
    "JockyTV.hu",
    "Kolyokklub.hu",
    "LifeTV.hu",
    "M1.hu",
    "M2.hu",
    "M4Sport.hu",
    "M5.hu",
    "MagyarMoziTV.hu",
    "Minimax.hu",
    "MoziPlus.hu",
    "Moziklub.hu",
    "Moziverzum.hu",
    "MuzsikaTV.hu",
    "NationalGeographic.hu",
    "NationalGeographicWild.hu",
    "NickJr.hu",
    "Nickelodeon.hu",
    "Nicktoons.hu",
    "OzoneTV.hu",
    "Prime.hu",
    "RTLGold.hu",
    "Spektrum.hu",
    "SuperTV2.hu",
    "TV2.hu",
    "TV4.hu",
    "Viasat3.hu",
    "Viasat6.hu",
    "ViasatFilm.hu"
}


def download():
    request = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        return response.read().decode(
            "utf-8",
            "replace"
        )


def main():

    print("IPTV-org lista letöltése...")

    data = download()

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

        first = block.splitlines()[0]

        match = re.search(
            r'tvg-id="([^"]+)"',
            first
        )

        if not match:
            continue

        channel_id = match.group(1)

        if channel_id not in ALLOWED:
            continue

        if channel_id in seen:
            continue

        seen.add(channel_id)
        result.append(block)

    def name(block):
        line = block.splitlines()[0]

        if "," in line:
            return line.split(",", 1)[1].lower()

        return ""

    result.sort(
        key=name
    )

    output = [
        "#EXTM3U",
        "# Magyar nyelvű országos TV csatornák",
        "# Helyi, városi, regionális és vallási csatornák nélkül"
    ]

    output.extend(result)

    OUTPUT.write_text(
        "\n\n".join(output) + "\n",
        encoding="utf-8"
    )

    print(
        "Forrás bejegyzések:",
        len(blocks)
    )

    print(
        "Engedélyezett csatornák:",
        len(result)
    )

    print(
        "magyar.m3u elkészült."
    )


if __name__ == "__main__":
    main()
