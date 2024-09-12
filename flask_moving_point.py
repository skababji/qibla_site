from flask import Flask, send_file, request
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from pygeodesy import ellipsoidalVincenty as ev
from geopy.geocoders import Nominatim
import io

app = Flask(__name__)

# Earth radius
R = 6371.0

# Helper function to convert geodetic to Cartesian coordinates
def geodetic_to_cartesian(lat, lon, alt=0):
    lat = np.radians(lat)
    lon = np.radians(lon)
    x = (R + alt) * np.cos(lat) * np.cos(lon)
    y = (R + alt) * np.cos(lat) * np.sin(lon)
    z = (R + alt) * np.sin(lat)
    return x, y, z

# Initialize geolocator
geolocator = Nominatim(user_agent="qibla")
source_lat_long = (40.7128, -74.0060)  # New York City
source_geodesy = ev.LatLon(*source_lat_long)
mecca_geopy = geolocator.geocode("Mecca")
mecca_lat_long = (mecca_geopy.latitude, mecca_geopy.longitude)
mecca_geodesy = ev.LatLon(*mecca_lat_long)

@app.route('/plot')
def generate_plot():
    # Get the slider value (distance from source in meters)
    distance_from_source = float(request.args.get('distance', 4000000))  # Default to 4000000 meters
    
    # Calculate moving point geodesy and Cartesian coordinates
    moving_point_geodesy = source_geodesy.destination(distance_from_source, source_geodesy.initialBearingTo(mecca_geodesy))
    moving_point_cartesian = geodetic_to_cartesian(moving_point_geodesy.lat, moving_point_geodesy.lon)

    # Create the plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot source, destination (Mecca), and moving point
    source_cartesian = geodetic_to_cartesian(*source_lat_long)
    mecca_cartesian = geodetic_to_cartesian(*mecca_lat_long)
    
    ax.scatter(*source_cartesian, color='blue', label='Source (NYC)')
    ax.scatter(*mecca_cartesian, color='red', label='Mecca')
    ax.scatter(*moving_point_cartesian, color='green', label='Moving Point')

    # Labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Moving Point Along Great Circle Path')

    # Adjust plot limits (optional)
    ax.set_xlim([-R, R])
    ax.set_ylim([-R, R])
    ax.set_zlim([-R, R])

    # Create an image buffer to send the plot as a PNG
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return send_file(img, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
