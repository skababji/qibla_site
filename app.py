from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from pygeodesy.ellipsoidalVincenty import LatLon as LatLon_e
from pygeodesy.sphericalTrigonometry import LatLon as LatLon_s

app = Flask(__name__)
geolocator = Nominatim(user_agent="qibla")
places = pd.read_csv('worldcities.csv')

@app.route('/')
def home():
    countries = np.insert(np.unique(places['country'].sort_values().values), 0, '').tolist()
    return render_template('index.html', countries=countries)

@app.route('/get_cities', methods=['POST'])
def get_cities():
    country = request.form['country']
    cities = np.unique(places[places['country'] == country]['city'].values).tolist()
    return jsonify(cities)

@app.route('/receive-data', methods=['POST'])
def receive_data():
    data = request.get_json()
    sliderValue = data['sliderValue']
    print(f'Received variable: {sliderValue}')
    return jsonify({"status": "success", "received_variable": sliderValue})

@app.route('/calculate_bearing', methods=['POST'])
def calculate_bearing():
    country = request.form['country']
    city = request.form['city']
    loc_query = {'city': city, 'country': country}
    loc = geolocator.geocode(loc_query)
    mecca = geolocator.geocode("Mecca")

    if not loc:
        return jsonify({"error": "Location not found"})
    
    i_elps = LatLon_e(loc.latitude, loc.longitude)
    m_elps = LatLon_e(mecca.latitude, mecca.longitude)
    i_sphr = LatLon_s(loc.latitude, loc.longitude)
    m_sphr = LatLon_s(mecca.latitude, mecca.longitude)
    
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
        "city_coords": f"{loc.latitude}, {loc.longitude}",
        "gc_initial_bearing":gc_initial_bearing,
        "gc_final_bearing":gc_final_bearing,
        "gc_distance": gc_dist
    })

if __name__ == '__main__':
    app.run(debug=True)
