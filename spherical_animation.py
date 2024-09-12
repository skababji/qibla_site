import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pygeodesy import ellipsoidalVincenty as ev
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="qibla")

# Convert geodetic coordinates (latitude, longitude) to Cartesian coordinates (x, y, z)
def geodetic_to_cartesian(lat, lon, alt=0):
    lat = np.radians(lat)
    lon = np.radians(lon)
    x = (R + alt) * np.cos(lat) * np.cos(lon)
    y = (R + alt) * np.cos(lat) * np.sin(lon)
    z = (R + alt) * np.sin(lat)
    return x, y, z

#retunrs distance in meters between two geodesy points
def get_distance(source_lat_long, dest_lat_long):
    source_geodesy=ev.LatLon(*source_lat_long)
    dest_geodesy=ev.LatLon(*dest_lat_long)
    distance = source_geodesy.distanceTo(dest_geodesy)
    return distance/1000 #In km
 

def get_arc_points(source_lat_long, dest_lat_long):
    # source conversions
    source_xyz = geodetic_to_cartesian(*source_lat_long)
    # Mecca conversions
    dest_xyz = geodetic_to_cartesian(*dest_lat_long)
    # Generate intermediate points along the arc  path
    n_points = 100
    points_geodesy = [ev.LatLon(*source_lat_long).intermediateTo(ev.LatLon(*dest_lat_long), i / n_points) for i in range(n_points)]
    intermediate_points_cartesian = [geodetic_to_cartesian(point.lat, point.lon) for point in points_geodesy]
    x_points = [point[0] for point in intermediate_points_cartesian]
    y_points = [point[1] for point in intermediate_points_cartesian]
    z_points = [point[2] for point in intermediate_points_cartesian]   
    return source_xyz, dest_xyz, x_points, y_points, z_points

# # Get the destination point along the great circle path    
# def animate_moving_point(distance_from_source):
#     moving_point_geodesy = source_geodesy.destination(distance_from_source*1000, source_geodesy.initialBearingTo(mecca_geodesy)) #1000 converts km to meter
#     moving_point_cartesian = geodetic_to_cartesian(moving_point_geodesy.lat, moving_point_geodesy.lon)
#     return moving_point_cartesian

def setup_plot(R):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
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
    return ax

 
def plot_arc(ax,x_points,y_points, source_xyz,dest_xyz, earth_center,north_pole_cartesian):
    # Create a figure and 3D axis
    ax.plot(x_points, y_points, z_points, 'b-')
    ax.plot([source_xyz[0]], [source_xyz[1]], [source_xyz[2]], 'ro')  # source
    ax.plot([dest_xyz[0]], [dest_xyz[1]], [dest_xyz[2]], 'go')  # Destination
    
    # Add labels
    ax.text(earth_center[0], earth_center[1], earth_center[2], '  Earth Center', fontsize=8, ha='right')
    ax.text(north_pole_cartesian[0], north_pole_cartesian[1], north_pole_cartesian[2], '  North Pole', fontsize=8, ha='right')
    ax.text(source_xyz[0], source_xyz[1], source_xyz[2], '  New York City', fontsize=8, ha='right')
    ax.text(dest_xyz[0], dest_xyz[1], dest_xyz[2], '  Mecca', fontsize=8, ha='right')
    return ax
    
def plot_moving_point(ax,moving_point_cartesian):  
    ax.text(moving_point_cartesian[0], moving_point_cartesian[1], moving_point_cartesian[2], '  Moving Point', fontsize=8, ha='right')



R = 6371.0 # Radius of the Earth in kilometers
north_pole_cartesian=(0,0,R)
earth_center=(0,0,0)
source_lat_long = (40.7128, -74.0060)  # New York City
mecca_geopy = geolocator.geocode("Mecca")
mecca_lat_long=(mecca_geopy.latitude, mecca_geopy.longitude)
source_xyz, dest_xyz, x_points, y_points, z_points=get_arc_points(source_lat_long, mecca_lat_long)
distance=get_distance(source_lat_long, mecca_lat_long) #in km
ax=setup_plot(R)
plot_arc(ax,x_points,y_points, source_xyz,dest_xyz, earth_center,north_pole_cartesian)


# Define step distance and find the corresponding steps array
step_distance= 200 #in km
step_distances=np.arange(0,full_distance,step_distance)



#Earth center an dnorth pole points in cartesian coordinates



#ax.plot([midpoint_cartesian[0]], [midpoint_cartesian[1]], [midpoint_cartesian[2]], 'bo')  # Midpoint
""" # Calculate the midpoint on the great circle path between source and destination
midpoint_geodesy = ev.LatLon(*source_lat_long).midpointTo(mecca_geodesy) """
for step_distance in step_distances:
    moving_point_geodesy = source_geodesy.destination(step_distances, source_geodesy.initialBearingTo(mecca_geodesy))
    moving_point_cartesian = geodetic_to_cartesian(moving_point_geodesy.lat, moving_point_geodesy.lon)
    ax.plot([moving_point_cartesian[0]], [moving_point_cartesian[1]], [moving_point_cartesian[2]], 'bo')  # Movingpoint


# Plot the red vector from the center of the Earth to the midpoint
ax.plot([earth_center[0], moving_point_cartesian[0]], [earth_center[1], moving_point_cartesian[1]], [earth_center[2], moving_point_cartesian[2]], 'r-')

# Plot the red vector from the center of the North Pole to the midpoint
ax.plot([north_pole_cartesian[0], moving_point_cartesian[0]], [north_pole_cartesian[1], moving_point_cartesian[1]], [north_pole_cartesian[2], moving_point_cartesian[2]], 'r-')

# # Plot the red vector from the center of the Earth to the source
# ax.plot([0, source_cartesian[0]], [0, source_cartesian[1]], [0, source_cartesian[2]], 'r-')








# #Remove axis lines
# plt.axis('off')

# Save the plot as an image file
plt.savefig('earth_plot_with_vectors.png')

# Close the figure to prevent it from being displayed interactively
plt.close(fig)
