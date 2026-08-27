# Magyar IPTV automatikus playlist

Ez a GitHub Actions workflow az iptv-org aktuális magyar nyelvű playlistjét tölti le,
majd kiszűri:
- a regionális/városi csatornákat,
- a vallási csatornákat,
- a rádiókat,
- a nem kívánt kategóriákat.

A létrejövő playlist: `magyar.m3u`

A GitHub Actions automatikusan frissíti naponta.

## Beállítás

1. Hozz létre egy GitHub repository-t (pl. `magyar-iptv`).
2. Töltsd fel a fájlokat ebbe a repository-ba.
3. A repository Settings → Pages alatt válaszd a GitHub Actions alapú publikálást, vagy
   egyszerűen használd a repository `raw.githubusercontent.com` URL-jét.
4. A bemásolható playlist URL-je:

`https://raw.githubusercontent.com/SAJAT_FELHASZNALO/magyar-iptv/main/magyar.m3u`

A `SAJAT_FELHASZNALO` részt a saját GitHub-felhasználónevedre kell cserélni.
