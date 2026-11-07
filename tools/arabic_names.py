"""Build arabic_names.csv: Arabic names for the cities in worldcities.csv (standard library only).

    python3 tools/arabic_names.py <geonames-dir> [--wikidata]

<geonames-dir> must contain these files from https://download.geonames.org/export/dump/
(GeoNames, CC BY 4.0):
    cities500.txt          (unzipped cities500.zip)
    alternateNamesV2.txt   (unzipped alternateNamesV2.zip)
    admin1CodesASCII.txt

Each city in worldcities.csv is matched to a GeoNames place in the same country, within
25 km, whose name matches (ignoring accents and case). Its Arabic name is taken from the
GeoNames alternate names (preferred name first; historic and colloquial names skipped),
and optionally (--wikidata) from the Arabic label of the linked Wikidata item (fetched
once, cached in <geonames-dir>/wikidata_ar.json). States/provinces get Arabic names the
same way. Cities without an Arabic name keep English.

The result is an internal mapping file keyed by the city id in worldcities.csv, with the
English names alongside so it can be read and corrected by hand.
"""
import csv
import json
import math
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_KM = 25
ARABIC = re.compile(r'[؀-ۿ]')
LATIN = re.compile(r'[A-Za-z]')
# Letters used in Persian/Urdu but not in Arabic: skip names written with them
# Persian/Urdu letters with an exact Arabic equivalent are converted (ی→ي, ک→ك, ھ→ه);
# names using letters Arabic does not have (پ چ ژ گ ں ے …) are skipped
TO_ARABIC = str.maketrans({'\u06CC': '\u064A', '\u06A9': '\u0643', '\u06BE': '\u0647'})
NON_ARABIC_LETTERS = re.compile(r'[\u067E\u0686\u0698\u06AF\u06BA\u06C0-\u06D3]')


def norm(name):
    text = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def load_geonames_cities(path):
    by_cell = defaultdict(list)   # (country, lat cell, lon cell) -> places
    with open(path, encoding='utf-8') as f:
        for line in f:
            c = line.rstrip('\n').split('\t')
            place = {
                'id': c[0], 'lat': float(c[4]), 'lon': float(c[5]), 'cc': c[8], 'admin1': c[10],
                'pop': int(c[14] or 0),
                'names': {norm(c[1]), norm(c[2])},
                'alt': {norm(n) for n in c[3].split(',') if n and LATIN.search(n)},
            }
            by_cell[(place['cc'], int(place['lat'] // 0.5), int(place['lon'] // 0.5))].append(place)
    return by_cell


def candidates(by_cell, cc, lat, lon):
    la, lo = int(lat // 0.5), int(lon // 0.5)
    for dla in (-1, 0, 1):
        for dlo in (-1, 0, 1):
            yield from by_cell.get((cc, la + dla, lo + dlo), [])


def best_match(by_cell, row):
    lat, lon = float(row['lat']), float(row['lng'])
    wanted = {norm(row['city']), norm(row['city_ascii'])}
    best = None
    for place in candidates(by_cell, row['iso2'], lat, lon):
        dist = km(lat, lon, place['lat'], place['lon'])
        if dist > MAX_KM:
            continue
        if wanted & place['names']:
            rank = (0, dist, -place['pop'])
        elif wanted & place['alt']:
            rank = (1, dist, -place['pop'])
        else:
            continue
        if best is None or rank < best[0]:
            best = (rank, place)
    return best[1] if best else None


def load_arabic_names(path, wanted_ids):
    """geonameid -> best Arabic name"""
    found = defaultdict(list)
    with open(path, encoding='utf-8') as f:
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) < 4 or c[2] != 'ar' or c[1] not in wanted_ids:
                continue
            name = clean_arabic(c[3])
            colloquial = len(c) > 6 and c[6] == '1'
            historic = len(c) > 7 and c[7] == '1'
            if colloquial or historic or not name:
                continue
            preferred = len(c) > 4 and c[4] == '1'
            short = len(c) > 5 and c[5] == '1'
            found[c[1]].append(((0 if preferred else 1, 1 if short else 0, len(name)), name))
    return found


def clean_arabic(name):
    """Arabic-script name without disambiguation suffixes, or '' if not usable."""
    name = name.translate(TO_ARABIC).strip()
    name = re.split(r'\s*[(،,]', name)[0].strip()   # "سبرينغفيلد (إلينوي)" -> "سبرينغفيلد"
    if not ARABIC.search(name) or LATIN.search(name) or NON_ARABIC_LETTERS.search(name):
        return ''
    return name


def wikidata_labels(geoname_ids, cache_path):
    """GeoNames id -> Arabic label of the linked Wikidata item (via property P1566)."""
    cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    todo = sorted(set(geoname_ids) - set(cache))
    for i in range(0, len(todo), 400):
        batch = todo[i:i + 400]
        query = ('SELECT ?gn ?label WHERE { VALUES ?gn { %s } ?item wdt:P1566 ?gn . '
                 '?item rdfs:label ?label . FILTER(LANG(?label) = "ar") }'
                 % ' '.join(f'"{g}"' for g in batch))
        request = urllib.request.Request(
            'https://query.wikidata.org/sparql',
            data=urllib.parse.urlencode({'query': query, 'format': 'json'}).encode(),
            headers={'User-Agent': 'qibla-site-build/1.0 (https://github.com/skababji/qibla_site)',
                     'Accept': 'application/sparql-results+json'})
        with urllib.request.urlopen(request, timeout=120) as response:
            results = json.load(response)['results']['bindings']
        for g in batch:
            cache.setdefault(g, '')
        for r in results:
            cache[r['gn']['value']] = r['label']['value']
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf-8')
        print(f'  Wikidata: {min(i + 400, len(todo)):,}/{len(todo):,}', file=sys.stderr)
    return {g: clean_arabic(cache.get(g, '')) for g in geoname_ids}


def choose(gid, geonames_found, wikidata):
    """Preferred GeoNames name, then Wikidata label, then any other GeoNames name."""
    names = sorted(geonames_found.get(gid, []))
    if names and names[0][0][0] == 0:
        return names[0][1]
    if wikidata.get(gid):
        return wikidata[gid]
    return names[0][1] if names else ''


def main(geonames_dir, use_wikidata=False):
    gdir = Path(geonames_dir)
    with (ROOT / 'worldcities.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))

    by_cell = load_geonames_cities(gdir / 'cities500.txt')
    matches = {row['id']: best_match(by_cell, row) for row in rows}

    admin1_ids = {}
    with (gdir / 'admin1CodesASCII.txt').open(encoding='utf-8') as f:
        for line in f:
            code, _name, _ascii, gid = line.rstrip('\n').split('\t')
            admin1_ids[code] = gid

    wanted = {p['id'] for p in matches.values() if p}
    wanted |= {admin1_ids[f"{p['cc']}.{p['admin1']}"] for p in matches.values()
               if p and f"{p['cc']}.{p['admin1']}" in admin1_ids}
    found = load_arabic_names(gdir / 'alternateNamesV2.txt', wanted)
    wikidata = wikidata_labels(wanted, gdir / 'wikidata_ar.json') if use_wikidata else {}
    arabic = {gid: choose(gid, found, wikidata) for gid in wanted}

    out = ROOT / 'arabic_names.csv'
    named = 0
    with out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'city', 'admin_name', 'country', 'city_ar', 'admin_ar', 'geonameid'])
        for row in rows:
            place = matches[row['id']]
            if not place:
                continue
            city_ar = arabic.get(place['id'], '')
            admin_ar = arabic.get(admin1_ids.get(f"{place['cc']}.{place['admin1']}", ''), '')
            if city_ar:
                named += 1
            if city_ar or admin_ar:
                writer.writerow([row['id'], row['city'], row['admin_name'], row['country'],
                                 city_ar, admin_ar, place['id']])
    matched = sum(1 for p in matches.values() if p)
    print(f'{len(rows):,} cities | matched to GeoNames: {matched:,} | with an Arabic name: {named:,} '
          f'({named / len(rows):.0%}) -> {out.relative_to(ROOT)}')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--wikidata']
    if len(args) != 1:
        sys.exit(__doc__)
    main(args[0], use_wikidata='--wikidata' in sys.argv[1:])
