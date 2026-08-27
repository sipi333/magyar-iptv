exec(compile('''import urllib.request
import re
from pathlib import Path

SOURCE = "https://iptv-org.github.io/iptv/languages/hun.m3u"
OUTPUT = Path("magyar.m3u")

BAD = ["radio","rádió","vallási","vallas","religious","christian","gospel","church","catholic","katolikus","reformatus","református","evangelikus","evangélikus","biblia","bible","jesus","jézus","jezus","városi","varosi","city tv","citytv","local tv","localtv","helyi tv","helyitv","térségi","tersegi","regionalis","regionális","regios","régiós","megyei","megye tv","kerületi","keruleti","district tv","municipal","onkormanyzati","önkormányzati"]

def norm(s):
return re.sub(r"\s+", " ", s.lower()).strip()

req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"})
data = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
lines = data.splitlines()
out = ["#EXTM3U"]
seen = set()
current = []

for line in lines:
line = line.strip()
if line.startswith("#EXTINF"):
if current:
text = norm(" ".join(current))
name = norm(current[0].split(",", 1)[-1])
if not any(x in text for x in BAD) and name not in seen:
out.extend(current)
seen.add(name)
current = [line]
elif current:
current.append(line)

if current:
text = norm(" ".join(current))
name = norm(current[0].split(",", 1)[-1])
if not any(x in text for x in BAD) and name not in seen:
out.extend(current)

OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
print("Kész:", OUTPUT)
print("Csatornák:", len(seen))
''', "<string>", "exec"))
