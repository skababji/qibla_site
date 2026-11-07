"""Build the static site into _site/ for GitHub Pages (standard library only).

    python3 build.py           # build _site/
    python3 build.py --serve   # build, then serve it at http://127.0.0.1:5050

Copies web/ to _site/, splits worldcities.csv into one small JSON file per country,
and adds a content hash to each static file link so browsers never use a stale copy.
"""
import argparse
import csv
import functools
import hashlib
import http.server
import json
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web'
OUT = ROOT / '_site'
CITIES_CSV = ROOT / 'worldcities.csv'
# Countries left out of the site entirely (both pages), by ISO code
EXCLUDED_COUNTRIES = {'IL'}
ARABIC_NAMES_CSV = ROOT / 'arabic_names.csv'   # made by tools/arabic_names.py


def slugify(name):
    ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', ascii_name.lower()).strip('-') or 'country'


def city_labels(rows, city_key='city', admin_key='admin_name', sep=', '):
    """Give each city a dropdown label that is unique within its country.

    A name used once in a country is shown as is ("Toronto"). A repeated name gets its
    state or province ("Springfield, Missouri"), and if that is still not unique, its
    coordinates too ("Springfield, Pennsylvania (39.93, -75.34)").
    """
    name_count = Counter(r[city_key] for r in rows)
    english_count = Counter(r['city'] for r in rows)  # keep Arabic labels as specific as English ones
    labels = []
    for r in rows:
        label = r[city_key]
        if (name_count[label] > 1 or english_count[r['city']] > 1) and r[admin_key]:
            label = f"{label}{sep}{r[admin_key]}"
        labels.append(label)
    label_count = Counter(labels)
    return [
        f"{label} ({float(r['lat']):.2f}, {float(r['lng']):.2f})" if label_count[label] > 1 else label
        for label, r in zip(labels, rows)
    ]


def load_arabic_names():
    """city id -> (Arabic city name, Arabic state/province name), either may be ''."""
    if not ARABIC_NAMES_CSV.exists():
        return {}
    with ARABIC_NAMES_CSV.open(encoding='utf-8', newline='') as f:
        return {r['id']: (r['city_ar'], r['admin_ar']) for r in csv.DictReader(f)}


def build_data(out_dir):
    arabic = load_arabic_names()
    with CITIES_CSV.open(encoding='utf-8', newline='') as f:
        by_country = defaultdict(list)
        for row in csv.DictReader(f):
            if row['iso2'] in EXCLUDED_COUNTRIES:
                continue
            # Arabic page: Arabic names where known, otherwise the English ones
            city_ar, admin_ar = arabic.get(row['id'], ('', ''))
            row['has_ar'] = bool(city_ar)
            row['city_ar'] = city_ar or row['city']
            row['admin_ar'] = admin_ar or row['admin_name']
            by_country[row['country']].append(row)

    countries, used_slugs = [], set()
    (out_dir / 'cities').mkdir(parents=True)
    for country in sorted(by_country, key=str.casefold):
        rows = by_country[country]
        slug = base = slugify(country)
        n = 2
        while slug in used_slugs:
            slug, n = f'{base}-{n}', n + 1
        used_slugs.add(slug)

        labels_en = city_labels(rows)
        labels_ar = city_labels(rows, 'city_ar', 'admin_ar', '، ')
        cities = sorted(
            # [English label, lat, lng] plus the Arabic label for cities with an Arabic name
            ([en, float(r['lat']), float(r['lng'])] + ([ar] if r['has_ar'] else [])
             for en, ar, r in zip(labels_en, labels_ar, rows)),
            key=lambda c: c[0].casefold(),
        )
        with (out_dir / 'cities' / f'{slug}.json').open('w', encoding='utf-8') as f:
            json.dump(cities, f, ensure_ascii=False, separators=(',', ':'))
        # [name, file, ISO code, number of cities with an Arabic name]
        countries.append([country, slug, rows[0]['iso2'], sum(r['has_ar'] for r in rows)])

    with (out_dir / 'countries.json').open('w', encoding='utf-8') as f:
        json.dump(countries, f, ensure_ascii=False, separators=(',', ':'))
    return len(countries), sum(len(rows) for rows in by_country.values())


def add_cache_busting(html_path):
    """static/x.js (or ../static/x.js) -> same path + ?v=<hash of the file>"""
    def versioned(match):
        path = match.group(1)
        file = (html_path.parent / path).resolve()
        if not file.is_file():
            return match.group(0)
        digest = hashlib.sha256(file.read_bytes()).hexdigest()[:10]
        return f'"{path}?v={digest}"'

    html = html_path.read_text(encoding='utf-8')
    html_path.write_text(re.sub(r'"((?:\.\./)*static/[^"?]+)"', versioned, html), encoding='utf-8')


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(WEB, OUT)
    countries, cities = build_data(OUT / 'data')
    for page in OUT.rglob('*.html'):
        add_cache_busting(page)
    (OUT / '.nojekyll').touch()
    print(f'Built {OUT.relative_to(ROOT)}/ with {cities:,} cities in {countries} countries')


def serve(port=5050):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    with http.server.ThreadingHTTPServer(('127.0.0.1', port), handler) as httpd:
        print(f'Serving at http://127.0.0.1:{port} (Ctrl+C to stop)')
        httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--serve', action='store_true', help='serve the built site locally')
    parser.add_argument('--port', type=int, default=5050)
    args = parser.parse_args()
    build()
    if args.serve:
        serve(args.port)
