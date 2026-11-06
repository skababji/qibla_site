import os

from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
from pygeodesy.ellipsoidalVincenty import LatLon as LatLon_e
from pygeodesy.sphericalTrigonometry import LatLon as LatLon_s

app = Flask(__name__)


@app.context_processor
def static_versioning():
    """static_url('x.js') adds the file's modification time so browsers never use a stale copy."""
    def static_url(filename):
        path = os.path.join(app.static_folder, filename)
        version = int(os.path.getmtime(path)) if os.path.exists(path) else 0
        return url_for('static', filename=filename, v=version)
    return {'static_url': static_url}

# The Kaaba, Masjid al-Haram, Makkah (latitude, longitude in degrees)
KAABA = (21.422487, 39.826206)

ROUTE_SAMPLES = 150  # points per route for the animation


def route_samples(total_m, point_at, bearing_at, final_bearing):
    """Sample a route for the animation as [lat, lon, bearing, remaining_km] rows."""
    rows = []
    for i in range(ROUTE_SAMPLES + 1):
        travelled = total_m * i / ROUTE_SAMPLES
        point = point_at(travelled)
        bearing = final_bearing if i == ROUTE_SAMPLES else bearing_at(point)
        rows.append([round(point.lat, 4), round(point.lon, 4), round(bearing % 360, 1),
                     round((total_m - travelled) / 1000)])
    return rows


def load_places(path='worldcities.csv'):
    """Load cities and give each one a dropdown label that is unique within its country.

    A name used once in a country is shown as is ("Toronto"). A repeated name gets its
    state or province ("Springfield, Missouri"), and if that is still not unique, its
    coordinates too ("Springfield, Pennsylvania (39.93, -75.34)").
    """
    places = pd.read_csv(path, dtype={'id': str})
    places['admin_name'] = places['admin_name'].fillna('')

    name_count = places.groupby(['country', 'city'])['city'].transform('size')
    with_admin = places['city'] + places['admin_name'].map(lambda a: f', {a}' if a else '')
    places['label'] = places['city'].where(name_count == 1, with_admin)

    label_count = places.groupby(['country', 'label'])['label'].transform('size')
    with_coords = places['label'] + places.apply(lambda r: f" ({r['lat']:.2f}, {r['lng']:.2f})", axis=1)
    places['label'] = places['label'].where(label_count == 1, with_coords)

    return places.sort_values('label', key=lambda col: col.str.casefold())


places = load_places()
places_by_id = places.set_index('id')
countries = sorted(places['country'].unique(), key=str.casefold)
cities_by_country = {
    country: group[['id', 'label']].to_dict('records')
    for country, group in places.groupby('country')
}


@app.route('/')
def home():
    return render_template('index.html', countries=countries)

@app.route('/get_cities', methods=['POST'])
def get_cities():
    country = request.form['country']
    return jsonify(cities_by_country.get(country, []))

@app.route('/receive-data', methods=['POST'])
def receive_data():
    data = request.get_json()
    sliderValue = data['sliderValue']
    print(f'Received variable: {sliderValue}')
    return jsonify({"status": "success", "received_variable": sliderValue})

@app.route('/calculate_bearing', methods=['POST'])
def calculate_bearing():
    city_id = request.form.get('city_id', '')
    if city_id not in places_by_id.index:
        return jsonify({"error": "Location not found"})
    place = places_by_id.loc[city_id]
    lat, lng = float(place['lat']), float(place['lng'])

    i_elps = LatLon_e(lat, lng)
    m_elps = LatLon_e(*KAABA)
    i_sphr = LatLon_s(lat, lng)
    m_sphr = LatLon_s(*KAABA)
    
    try:
        # rhumb line (sphere): one constant bearing all the way
        rhumb_bearing_exact = i_sphr.rhumbBearingTo(m_sphr)
        rhumb_dist_m = i_sphr.rhumbDistanceTo(m_sphr)

        # great circle (WGS-84 ellipsoid): bearing changes along the route
        gc_initial_exact = i_elps.initialBearingTo(m_elps)
        gc_final_exact = i_elps.finalBearingTo(m_elps)
        gc_dist_m = i_elps.distanceTo(m_elps)

        paths = {
            "rhumb": route_samples(
                rhumb_dist_m,
                point_at=lambda d: i_sphr.rhumbDestination(d, rhumb_bearing_exact),
                bearing_at=lambda p: rhumb_bearing_exact,
                final_bearing=rhumb_bearing_exact),
            "gc": route_samples(
                gc_dist_m,
                point_at=lambda d: i_elps.destination(d, gc_initial_exact),
                bearing_at=lambda p: p.initialBearingTo(m_elps),
                final_bearing=gc_final_exact),
        }
    except Exception:  # e.g. Vincenty not converging for a nearly antipodal city
        return jsonify({"error": "Could not calculate the route for this city"})

    return jsonify({
        "rhumb_bearing": round(rhumb_bearing_exact, 0),
        "rhumb_distance": round(rhumb_dist_m / 1000, 0),
        "city_coords": f"{lat}, {lng}",
        "gc_initial_bearing": round(gc_initial_exact, 0),
        "gc_final_bearing": str(round(gc_final_exact, 0)),
        "gc_distance": round(gc_dist_m / 1000, 0),
        "kaaba": KAABA,
        "paths": paths,
    })

if __name__ == '__main__':
    app.run(debug=True, port=5050)  # 5000 is used by AirPlay on macOS
