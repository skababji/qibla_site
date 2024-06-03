import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pygeodesy import ellipsoidalVincenty as ev
from geopy.geocoders import Nominatim


geolocator = Nominatim(user_agent="qibla")


# Radius of the Earth in kilometers
R = 6371.0

# Convert geodetic coordinates (latitude, longitude) to Cartesian coordinates (x, y, z)
def geodetic_to_cartesian(lat, lon, alt=0):
    lat = np.radians(lat)
    lon = np.radians(lon)
    x = (R + alt) * np.cos(lat) * np.cos(lon)
    y = (R + alt) * np.cos(lat) * np.sin(lon)
    z = (R + alt) * np.sin(lat)
    return x, y, z

# Define the source and destination coordinates (latitude, longitude)
source_lat_long = (40.7128, -74.0060)  # New York City
source_geodesy=ev.LatLon(*source_lat_long)

mecca_geopy = geolocator.geocode("Mecca")
mecca_lat_long=(mecca_geopy.latitude, mecca_geopy.longitude)
mecca_geodesy=ev.LatLon(*mecca_lat_long)
#destination = (34.0522, -118.2437)  # Los Angeles


""" # Calculate the midpoint on the great circle path between source and destination
midpoint_geodesy = ev.LatLon(*source_lat_long).midpointTo(mecca_geodesy) """


# Get the destination point along the great circle path
distance_from_source=4000000 #in meters
moving_point_geodesy = source_geodesy.destination(distance_from_source, source_geodesy.initialBearingTo(mecca_geodesy))


# Generate intermediate points along the great circle path
n_points = 100
points_geodesy = [ev.LatLon(*source_lat_long).intermediateTo(ev.LatLon(*mecca_lat_long), i / n_points) for i in range(n_points)]

# Convert source, destination, and midpoint to Cartesian coordinates
source_cartesian = geodetic_to_cartesian(*source_lat_long)
mecca_cartesian = geodetic_to_cartesian(*mecca_lat_long)
#midpoint_cartesian = geodetic_to_cartesian(midpoint_geodesy.lat, midpoint_geodesy.lon)
moving_point_cartesian = geodetic_to_cartesian(moving_point_geodesy.lat, moving_point_geodesy.lon)


#Earth center an dnorth pole points in cartesian coordinates
north_pole_cartesian=(0,0,R)
earth_center=(0,0,0)

# Create a figure and 3D axis
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection='3d')

# Plot great circle path  in Cartesian coordinates
intermediate_points_cartesian = [geodetic_to_cartesian(point.lat, point.lon) for point in points_geodesy]
x_points = [point[0] for point in intermediate_points_cartesian]
y_points = [point[1] for point in intermediate_points_cartesian]
z_points = [point[2] for point in intermediate_points_cartesian]
ax.plot(x_points, y_points, z_points, 'b-')

# Plot the source, destination, and midpoint points
ax.plot([source_cartesian[0]], [source_cartesian[1]], [source_cartesian[2]], 'ro')  # source
ax.plot([mecca_cartesian[0]], [mecca_cartesian[1]], [mecca_cartesian[2]], 'go')  # Destination
#ax.plot([midpoint_cartesian[0]], [midpoint_cartesian[1]], [midpoint_cartesian[2]], 'bo')  # Midpoint
ax.plot([moving_point_cartesian[0]], [moving_point_cartesian[1]], [moving_point_cartesian[2]], 'bo')  # Movingpoint


# Plot the red vector from the center of the Earth to the midpoint
ax.plot([earth_center[0], moving_point_cartesian[0]], [earth_center[1], moving_point_cartesian[1]], [earth_center[2], moving_point_cartesian[2]], 'r-')

# Plot the red vector from the center of the North Pole to the midpoint
ax.plot([north_pole_cartesian[0], moving_point_cartesian[0]], [north_pole_cartesian[1], moving_point_cartesian[1]], [north_pole_cartesian[2], moving_point_cartesian[2]], 'r-')

# # Plot the red vector from the center of the Earth to the source
# ax.plot([0, source_cartesian[0]], [0, source_cartesian[1]], [0, source_cartesian[2]], 'r-')

# Add labels
ax.text(earth_center[0], earth_center[1], earth_center[2], '  Earth Center', fontsize=8, ha='right')
ax.text(north_pole_cartesian[0], north_pole_cartesian[1], north_pole_cartesian[2], '  North Pole', fontsize=8, ha='right')
ax.text(source_cartesian[0], source_cartesian[1], source_cartesian[2], '  New York City', fontsize=8, ha='right')
ax.text(mecca_cartesian[0], mecca_cartesian[1], mecca_cartesian[2], '  Mecca', fontsize=8, ha='right')
ax.text(moving_point_cartesian[0], moving_point_cartesian[1], moving_point_cartesian[2], '  Moving Point', fontsize=8, ha='right')


# Set axis limits
ax.set_xlim([0, R])
ax.set_ylim([-R, R])
ax.set_zlim([0, R])


# Plot the main axes
ax.plot([0, R], [0, 0], [0, 0], 'k-')  # X-axis
ax.plot([0, 0], [-R, R], [0, 0], 'k-')  # Y-axis
ax.plot([0, 0], [0, 0], [0, R], 'k-')  # Z-axis

# Set axis labels and title
ax.set_xlabel('') #'X'
ax.set_ylabel('')
ax.set_zlabel('')

#Remove ticks
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.set_zticklabels([])

plt.title('Great Circle Path')

# Set box aspect to control zoom in and out
ax.set_box_aspect([1, 1, 1])


# #Remove axis lines
# plt.axis('off')

# Save the plot as an image file
plt.savefig('earth_plot_with_vectors.png')

# Close the figure to prevent it from being displayed interactively
plt.close(fig)
