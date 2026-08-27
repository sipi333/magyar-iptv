import json
import urllib.request
from pathlib import Path


API = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API}/channels.json"
FEEDS_URL = f"{API}/feeds.json"
STREAMS_URL = f"{API}/streams.json"
LOGOS_URL = f"{API}/logos.json"

OUTPUT = Path("magyar.m3u")


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"
