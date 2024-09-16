import os
import numpy as np

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="qibla")

#from pygeodesy import ellipsoidalVincenty as earth_model #used for great circle. does not support rhumb line calc
from pygeodesy import sphericalTrigonometry as earth_model #used here forrhumb lne calc (but can be also usd for great curcle calc) 
from pygeodesy import  rhumb

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image


# Convert geodetic coordinates (latitude, longitude) to Cartesian coordinates (x, y, z)
def geodetic_to_cartesian(lat, lon, alt=0):
    lat = np.radians(lat)
    lon = np.radians(lon)
    x = (R + alt) * np.cos(lat) * np.cos(lon)
    y = (R + alt) * np.cos(lat) * np.sin(lon)
    z = (R + alt) * np.sin(lat)
    return x, y, z

#plots a sphere
def plot_sphere(ax,radius, show_grid=False):
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))# Plot the surface of the sphere
    ax.plot_surface(x, y, z, color='cyan', alpha=0.05, edgecolor='none')  # light and transparent
    
    if show_grid: 
        # Add latitude and longitude grid lines
        num_lat_lines = 5
        num_lon_lines = 5

        # Latitude lines (parallel to the xy-plane)
        for i in range(num_lat_lines):
            theta = i * 2 * np.pi / num_lat_lines
            x_lat = R * np.cos(theta)
            y_lat = R * np.sin(theta)
            z_lat = np.zeros_like(x_lat)
            ax.plot(x_lat, y_lat, z_lat, color='cyan', alpha=0.2)

        # Longitude lines (meridians)
        for i in range(num_lon_lines):
            phi = i * np.pi / num_lon_lines
            x_lon = R * np.sin(phi) * np.cos(u)
            y_lon = R * np.sin(phi) * np.sin(u)
            z_lon = R * np.cos(phi) * np.ones_like(u)
            ax.plot(x_lon, y_lon, z_lon, color='cyan', alpha=0.2)

    # Set the aspect ratio to ensure the sphere looks like a sphere
    ax.set_box_aspect([1, 1, 1])
    
    return ax

    

#retunrs distance in meters between two geodesy points
def get_distance(source_geodesy, dest_geodesy, route="great_circle"):
    if route=='great_circle':
        distance = source_geodesy.distanceTo(dest_geodesy)
    elif route=='rhumb_line':
        distance = source_geodesy.rhumbDistanceTo(dest_geodesy)
    else:
        raise TypeError
    return distance/1000 #In km

def get_xyz4arc_points(source_geodesy, dest_geodesy, n_points=100, route="great_circle"):
    if route=='great_circle':
        points_geodesy = [source_geodesy.intermediateTo(dest_geodesy, i / n_points) for i in range(n_points)]
    elif route=='rhumb_line':
        points_geodesy=[]
        rhumb_bearing = source_geodesy.rhumbBearingTo(dest_geodesy)
        rhumb_dist = source_geodesy.rhumbDistanceTo(dest_geodesy)
        for i in range(n_points):
            step_point= source_geodesy.rhumbDestination( i*rhumb_dist/n_points,rhumb_bearing)
            points_geodesy.append(step_point)
    else:
        raise TypeError
    intermediate_points_cartesian = [geodetic_to_cartesian(point.lat, point.lon) for point in points_geodesy]
    x_points = [point[0] for point in intermediate_points_cartesian]
    y_points = [point[1] for point in intermediate_points_cartesian]
    z_points = [point[2] for point in intermediate_points_cartesian]   
    return  x_points, y_points, z_points

def get_xyz4moving_point(source_geodesy, dest_geodesy, moving_point_distance_from_source_kms, route="great_circle"):  
    moving_point_distance_from_source=moving_point_distance_from_source_kms*1000 #vonvert to meters
    if route=='great_circle':
        moving_point_geodesy = source_geodesy.destination(moving_point_distance_from_source, source_geodesy.initialBearingTo(dest_geodesy))
    elif route=='rhumb_line':
        rhumb_bearing = source_geodesy.rhumbBearingTo(dest_geodesy)
        moving_point_geodesy= source_geodesy.rhumbDestination(moving_point_distance_from_source,rhumb_bearing)

    moving_point_xyz = geodetic_to_cartesian(moving_point_geodesy.lat, moving_point_geodesy.lon)
    return moving_point_xyz


def setup_plot(ax,R, route_name):
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

    plt.title(f'{route_name} Trajectory')
    
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


'''' In this scrpt we efer to any pint on earth by four representaions:
1)point_geopy=geolocator.geocode(source_city_name)
2)point_latlong_tuple=(point_geopy.latitude,point_geopy.longitude)
3) point_pygeodesy=earth_model.LatLon(*point_latlong_tuple)
4)point_xyz_tuple=geodetic_to_cartesian(*point_latlong_tuple)
'''
R = 6371.0 # Radius of the Earth in kilometers
ROUTE="rhumb_line" #"rhumb_line"
north_pole_xyz_tuple=(0,0,R)
earth_center_xyz_tuple=(0,0,0)

source_city_name="Vancouver"
source_geopy = geolocator.geocode(source_city_name)
#source_latlong_tuple = (40.7128, -74.0060)  # New York City
source_latlong_tuple=(source_geopy.latitude, source_geopy.longitude)
mecca_geopy = geolocator.geocode("Mecca")
mecca_latlong_tuple=(mecca_geopy.latitude, mecca_geopy.longitude)

source_geodesy=earth_model.LatLon(*source_latlong_tuple)
mecca_geodesy=earth_model.LatLon(*mecca_latlong_tuple)

full_distance=get_distance(source_geodesy, mecca_geodesy,route=ROUTE) #in km
x_points, y_points, z_points=get_xyz4arc_points(source_geodesy, mecca_geodesy, n_points=100,route=ROUTE)

source_xyz_tuple=geodetic_to_cartesian(*source_latlong_tuple)
mecca_xyz_tuple=geodetic_to_cartesian(*mecca_latlong_tuple)

step_distance= 1000 #in km
distances=np.arange(0,full_distance,step_distance)
frames=[]
for i,moved_distance in enumerate(distances):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
    setup_plot(ax,R, ROUTE)
    plot_sphere(ax,R)
    plot_arc(ax,x_points,y_points, z_points, source_xyz_tuple,mecca_xyz_tuple, earth_center_xyz_tuple,north_pole_xyz_tuple, source_city_name)
    moving_point_xyz=get_xyz4moving_point(source_geodesy,mecca_geodesy, moved_distance,route=ROUTE)
    plot_moving_point(ax,earth_center_xyz_tuple,north_pole_xyz_tuple,moving_point_xyz)
    zenith_angle=np.arccos(moving_point_xyz[2]/R) #aka polar angle or theta i.e. angle wrt to z axis
    zenith_angle_opposite=R*np.sin(zenith_angle)
    angle_wrt_earth_center_text= f"{(180/np.pi)*zenith_angle:.0f}$^\\circ$"
    ax.text(700, 0, 1000, angle_wrt_earth_center_text, fontsize=8, ha='right')

    angle_wrt_north_pole_text=f"{(180/np.pi)*np.arctan(zenith_angle_opposite/(R-moving_point_xyz[2])):.0f}$^\\circ$"
    ax.text(north_pole_xyz_tuple[0]+700, north_pole_xyz_tuple[1], north_pole_xyz_tuple[2]-800, angle_wrt_north_pole_text, fontsize=8, ha='right')

    # Save the current figure as an image (PNG format)
    ax.view_init(elev=30, azim=-45) # defaults 30,-60
    frame_filename = f'frame_{i}.png'
    fig.savefig(frame_filename)
    
    # Open the image and add it to the frames list
    frames.append(Image.open(frame_filename))

# Save the frames as a GIF
frames[0].save(f'{ROUTE}_trajectory.gif', save_all=True, append_images=frames[1:], duration=1000, loop=0)

# Delete the individual frame files
for i in range(len(distances)):
    os.remove(f'frame_{i}.png')



# from pygeodesy import rhumb, LatLon

# source = LatLon(34.052235, -118.243683)  # Los Angeles
# destination = LatLon(40.712776, -74.005974)  # New York

# rhumb_line = source.rhumbTo(destination)

# # Calculate distance and intermediate points
# distance = rhumb_line.distance
# bearing = rhumb_line.bearing

# intermediate_point = source.rhumbAt(bearing, distance / 2)  # Middle of the rhumb line path

# print(f"Distance: {distance} km")
# print(f"Bearing: {bearing} degrees")
# print(f"Intermediate Point: {intermediate_point.lat}, {intermediate_point.lon}")

