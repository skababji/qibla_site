import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

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

def get_xyz4arc_points(source_lat_long, dest_lat_long, n_points=100):
    source_xyz = geodetic_to_cartesian(*source_lat_long)
    dest_xyz = geodetic_to_cartesian(*dest_lat_long)
    points_geodesy = [ev.LatLon(*source_lat_long).intermediateTo(ev.LatLon(*dest_lat_long), i / n_points) for i in range(n_points)]
    intermediate_points_cartesian = [geodetic_to_cartesian(point.lat, point.lon) for point in points_geodesy]
    x_points = [point[0] for point in intermediate_points_cartesian]
    y_points = [point[1] for point in intermediate_points_cartesian]
    z_points = [point[2] for point in intermediate_points_cartesian]   
    return source_xyz, dest_xyz, x_points, y_points, z_points

def get_xyz4moving_point(source_lat_long, dest_lat_long, moving_point_distance_from_source_kms):
    moving_point_distance_from_source=moving_point_distance_from_source_kms*1000 #vonvert to meters
    source_geodesy=ev.LatLon(*source_lat_long)
    dest_geodesy=ev.LatLon(*dest_lat_long)
    moving_point_geodesy = source_geodesy.destination(moving_point_distance_from_source, source_geodesy.initialBearingTo(dest_geodesy))
    moving_point_xyz = geodetic_to_cartesian(moving_point_geodesy.lat, moving_point_geodesy.lon)
    return moving_point_xyz


def setup_plot(ax,R):

    # Set axis limits
    ax.set_xlim([0, R])
    ax.set_ylim([-2.7*R, R])
    ax.set_zlim([0, 1.3*R])
    
    # Plot the main axes
    ax.plot([0, R], [0, 0], [0, 0], 'k-')  # X-axis
    ax.plot([0, 0], [-2.7*R, R], [0, 0], 'k-')  # Y-axis
    ax.plot([0, 0], [0, 0], [0, 1.3*R], 'k-')  # Z-axis

    # Set axis labels and title
    ax.set_xlabel('') #'X'
    ax.set_ylabel('')
    ax.set_zlabel('')

    #Remove ticks
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])

    plt.title('Great Circle Trajector')
    
    # Set box aspect to control zoom in and out
    ax.set_box_aspect([1, 1, 1])
    return ax

 
def plot_arc(ax,x_points,y_points, z_points, source_xyz,dest_xyz, earth_center,north_pole_xyz, source_city_name):
    # Create a figure and 3D axis
    ax.plot(x_points, y_points, z_points, 'b-')
    ax.plot([source_xyz[0]], [source_xyz[1]], [source_xyz[2]], 'ro')  # source
    ax.plot([dest_xyz[0]], [dest_xyz[1]], [dest_xyz[2]], 'go')  # Destination
    
    # Add labels
    ax.text(earth_center[0], earth_center[1], earth_center[2], '  Earth Center', fontsize=8, ha='right')
    ax.text(north_pole_xyz[0], north_pole_xyz[1], north_pole_xyz[2], '  North Pole', fontsize=8, ha='right')
    ax.text(source_xyz[0], source_xyz[1], source_xyz[2], f'  {source_city_name}', fontsize=8, ha='right')
    ax.text(dest_xyz[0], dest_xyz[1], dest_xyz[2], '  Mecca', fontsize=8, ha='right')
    return ax
    
def plot_moving_point(ax,earth_center_xyz,north_pole_xyz, moving_point_xyz):  
    ax.plot([moving_point_xyz[0]], [moving_point_xyz[1]], [moving_point_xyz[2]], 'bo')  # Movingpoint
    # ax.text(moving_point_cartesian[0], moving_point_cartesian[1], moving_point_cartesian[2], '  Moving Point', fontsize=8, ha='right')
    # Plot the red vector from the center of the Earth to the moving_point_cartesian
    ax.plot([earth_center_xyz[0], moving_point_xyz[0]], [earth_center_xyz[1], moving_point_xyz[1]], [earth_center_xyz[2], moving_point_xyz[2]], 'r-')
    # Plot the red vector from the center of the North Pole to the moving_point_cartesian
    ax.plot([north_pole_xyz[0], moving_point_xyz[0]], [north_pole_xyz[1], moving_point_xyz[1]], [north_pole_xyz[2], moving_point_xyz[2]], 'r-')



R = 6371.0 # Radius of the Earth in kilometers
north_pole_xyz=(0,0,R)
earth_center_xyz=(0,0,0)
source_city_name="Vancouver"
sourc_geopy = geolocator.geocode(source_city_name)
#source_lat_long = (40.7128, -74.0060)  # New York City
source_lat_long=(sourc_geopy.latitude, sourc_geopy.longitude)
mecca_geopy = geolocator.geocode("Mecca")
mecca_lat_long=(mecca_geopy.latitude, mecca_geopy.longitude)
source_xyz, dest_xyz, x_points, y_points, z_points=get_xyz4arc_points(source_lat_long, mecca_lat_long)
full_distance=get_distance(source_lat_long, mecca_lat_long) #in km


step_distance= 1000 #in km
distances=np.arange(0,full_distance,step_distance)
frames=[]
for i,moved_distance in enumerate(distances):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
    setup_plot(ax,R)
    plot_arc(ax,x_points,y_points, z_points, source_xyz,dest_xyz, earth_center_xyz,north_pole_xyz, source_city_name)
    moving_point_xyz=get_xyz4moving_point(source_lat_long,mecca_lat_long, moved_distance)
    plot_moving_point(ax,earth_center_xyz,north_pole_xyz,moving_point_xyz)
    zenith_angle=np.arccos(moving_point_xyz[2]/R) #aka polar angle or theta i.e. angle wrt to z axis
    zenith_angle_opposite=R*np.sin(zenith_angle)
    angle_wrt_earth_center_text= f"{(180/np.pi)*zenith_angle:.0f}$^\\circ$"
    ax.text(700, 0, 1000, angle_wrt_earth_center_text, fontsize=8, ha='right')

    angle_wrt_north_pole_text=f"{(180/np.pi)*np.arctan(zenith_angle_opposite/(R-moving_point_xyz[2])):.0f}$^\\circ$"
    ax.text(north_pole_xyz[0]+700, north_pole_xyz[1], north_pole_xyz[2]-800, angle_wrt_north_pole_text, fontsize=8, ha='right')

    # Save the current figure as an image (PNG format)
    frame_filename = f'frame_{i}.png'
    fig.savefig(frame_filename)
    
    # Open the image and add it to the frames list
    frames.append(Image.open(frame_filename))

# Save the frames as a GIF
frames[0].save('great_circle_trajectory.gif', save_all=True, append_images=frames[1:], duration=1000, loop=0)

# Delete the individual frame files
for i in range(len(distances)):
    os.remove(f'frame_{i}.png')

