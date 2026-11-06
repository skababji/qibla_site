from flask import Flask, render_template, request, jsonify
import pandas as pd
from pygeodesy.ellipsoidalVincenty import LatLon as LatLon_e
from pygeodesy.sphericalTrigonometry import LatLon as LatLon_s

app = Flask(__name__)

# The Kaaba, Masjid al-Haram, Makkah (latitude, longitude in degrees)
KAABA = (21.422487, 39.826206)


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
    
    #rhumb line calc
    rhumb_bearing = round(i_sphr.rhumbBearingTo(m_sphr), 0)
    rhumb_dist = round(i_sphr.rhumbDistanceTo(m_sphr) / 1000, 0)
    
    #great circlecalc
    gc_initial_bearing=round(i_elps.initialBearingTo(m_elps), 0)
    gc_final_bearing=str(round(i_elps.finalBearingTo(m_elps), 0))
    gc_dist=round(i_elps.distanceTo(m_elps)/1000, 0)
    
    return jsonify({
        "rhumb_bearing": rhumb_bearing,
        "rhumb_distance": rhumb_dist,
        "city_coords": f"{lat}, {lng}",
        "gc_initial_bearing":gc_initial_bearing,
        "gc_final_bearing":gc_final_bearing,
        "gc_distance": gc_dist
    })

if __name__ == '__main__':
    app.run(debug=True, port=5050)  # 5000 is used by AirPlay on macOS
