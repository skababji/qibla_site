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

#################################
ROUTES={
    "great_circle": "Great Circle (Orthodrome)",
    "rhumb_line": "Rhumb Line (Loxodrome)"
}

ROUTE_COLORS={
    "great_circle":"lightcoral",
    "rhumb_line":"lightgreen",
}

ROUTE_COMMENTS={
    "great_circle":"The orthodrome\ndeviates from\nthe reference point\nas defined by the Shariah",
    "rhumb_line":"The loxodrome\napproximates \nthe reference point\nas defined by the Shariah",
}
# ROUTES={
#     "great_circle": "great_circle",
# }

CITIES=["Toronto", "Vancouver", "Santiago"]
# CITIES=["Vancouver"]
R = 6371.0 # Radius of the Earth in kilometers
KAABA = (21.422487, 39.826206) # The Kaaba, Masjid al-Haram, Makkah (lat, lon)



##################################
def get_point_on_3d_line(source_xyz: tuple, dest_xyz: tuple ,dist_from_source: float ) -> tuple:
    source_xyz=np.array(source_xyz)
    dest_xyz=np.array(dest_xyz)
    source_dest_distance=np.linalg.norm(dest_xyz - source_xyz)
    source_dest_direction = (dest_xyz - source_xyz) / source_dest_distance
    point_xyz = source_xyz + dist_from_source * source_dest_direction
    return point_xyz


def bearing_to_direction(bearing):
    # Define the 16 compass directions
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    
    # Divide the bearing into 16 sectors of 22.5° each
    index = int((bearing + 11.25) // 22.5) % 16
    
    return directions[index]





# Convert geodetic coordinates (latitude, longitude) to Cartesian coordinates (x, y, z)
def geodetic_to_cartesian(lat, lon, alt=0):
    lat = np.radians(lat)
    lon = np.radians(lon)
    x = (R + alt) * np.cos(lat) * np.cos(lon)
    y = (R + alt) * np.cos(lat) * np.sin(lon)
    z = (R + alt) * np.sin(lat)
    return x, y, z

#plots a sphere
def plot_sphere(ax,radius, show_grid=True):
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))# Plot the surface of the sphere
    ax.plot_surface(x, y, z, color='cyan', alpha=0.1, edgecolor='none')  # light and transparent
    
    if show_grid: 
        # Add latitude and longitude grid lines
        num_lat_lines = 10
        num_lon_lines = 10

        # Latitude lines (parallel to the xy-plane)
        for i in range(num_lat_lines):
            theta = i * 2 * np.pi / num_lat_lines
            x_lat = R * np.cos(theta)
            y_lat = R * np.sin(theta)
            z_lat = np.zeros_like(x_lat)
            ax.plot(x_lat, y_lat, z_lat, color='gray', alpha=0.2)

        # Longitude lines (meridians)
        for i in range(num_lon_lines):
            phi = i * np.pi / num_lon_lines
            x_lon = R * np.sin(phi) * np.cos(u)
            y_lon = R * np.sin(phi) * np.sin(u)
            z_lon = R * np.cos(phi) * np.ones_like(u)
            ax.plot(x_lon, y_lon, z_lon, color='gray', alpha=0.2)

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
        bearing_to_dest= moving_point_geodesy.initialBearingTo(dest_geodesy)
    elif route=='rhumb_line':
        rhumb_bearing = source_geodesy.rhumbBearingTo(dest_geodesy)
        moving_point_geodesy= source_geodesy.rhumbDestination(moving_point_distance_from_source,rhumb_bearing)
        bearing_to_dest=rhumb_bearing
    moving_point_xyz = geodetic_to_cartesian(moving_point_geodesy.lat, moving_point_geodesy.lon)
    return moving_point_xyz, bearing_to_dest


def setup_plot(ax,R, route_name):
    # Set axis limits
    ax.set_xlim([-R, R])
    ax.set_ylim([-R, R])
    ax.set_zlim([-R, R])
    
    # Plot the main axes
    ax.plot([-1.5*R, 1.5*R], [0, 0], [0, 0], 'k-.', alpha=0.5)  # X-axis
    ax.plot([0, 0], [-1.5*R, 1.5*R], [0, 0], 'k-.',alpha=0.5)  # Y-axis
    ax.plot([0, 0], [0, 0], [-1.5*R, 1.5*R], 'k-.',alpha=0.5)  # Z-axis

    # Set axis labels and title
    ax.set_xlabel('') #'X'
    ax.set_ylabel('')
    ax.set_zlabel('')

    #Remove ticks
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])
    
    
    # Hide the background panes (these are the bold lines)
    ax.xaxis.pane.set_visible(False)  # Hide X-axis plane
    ax.yaxis.pane.set_visible(False)  # Hide Y-axis plane
    ax.zaxis.pane.set_visible(False)  # Hide Z-axis plane

    # Hide the bold axis lines by setting their color to none
    ax.xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))  # Make X-axis line invisible
    ax.yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))  # Make Y-axis line invisible
    ax.zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))  # Make Z-axis line invisible

    # Keep the grid visible
    ax.grid(True)

    plt.title(f'The {route_name} Route to Mecca',fontsize=18)
    
    # Set box aspect to control zoom in and out
    ax.set_box_aspect([1, 1, 1])

    return ax

 
def plot_arc(ax,x_points,y_points, z_points, source_xyz,dest_xyz, earth_center,north_pole_xyz, source_city_name):
    # Create a figure and 3D axis
    ax.plot(x_points, y_points, z_points, 'b-')
    ax.plot([source_xyz[0]], [source_xyz[1]], [source_xyz[2]], 'ro')  # source
    ax.plot([dest_xyz[0]], [dest_xyz[1]], [dest_xyz[2]], 'go')  # Destination
    
    # Add labels
    ax.text(earth_center[0], earth_center[1], earth_center[2]-600, '  Earth Center', fontsize=10, ha='center',va='center')
    ax.text(north_pole_xyz[0], north_pole_xyz[1], north_pole_xyz[2]+600, '  North Pole', fontsize=10, ha='center',va='center')
    ax.text(source_xyz[0], source_xyz[1], source_xyz[2], f'  {source_city_name}', fontsize=10, ha='right')
    ax.text(dest_xyz[0], dest_xyz[1], dest_xyz[2], '  Mecca', fontsize=10, ha='right')
    return ax
    
def plot_moving_point(ax,earth_center_xyz,north_pole_xyz, moving_point_xyz):  
    ax.plot([moving_point_xyz[0]], [moving_point_xyz[1]], [moving_point_xyz[2]], 'bo')  # Movingpoint
    # ax.text(moving_point_cartesian[0], moving_point_cartesian[1], moving_point_cartesian[2], '  Moving Point', fontsize=8, ha='right')
    
    '''
    # Plot the red vector from the center of the Earth to the moving_point_cartesian
    ax.plot([earth_center_xyz[0], moving_point_xyz[0]], [earth_center_xyz[1], moving_point_xyz[1]], [earth_center_xyz[2], moving_point_xyz[2]], 'r-')
    '''
    
    # Plot the red vector from the center of the North Pole to the moving_point_cartesian
    ax.plot([north_pole_xyz[0], moving_point_xyz[0]], [north_pole_xyz[1], moving_point_xyz[1]], [north_pole_xyz[2], moving_point_xyz[2]], linestyle='-',color=ROUTE_COLORS[route_abbr])
    

    symbol_dist=1000 # distance from origin where the arc is drawn 

    '''
    ##### angle symbol wrt earth center
    #get point on the z axis
    arc_point_on_z=get_point_on_3d_line(earth_center_xyz,north_pole_xyz,symbol_dist)
    # ax.plot(arc_point_on_z[0],arc_point_on_z[1],arc_point_on_z[2], marker='x', color='black', markersize=2, linestyle='None')
    #plot
    arc_point_on_vec=get_point_on_3d_line(earth_center_xyz,moving_point_xyz,symbol_dist)
    # ax.plot(arc_point_on_vec[0],arc_point_on_vec[1],arc_point_on_vec[2],marker='x', color='black', markersize=2, linestyle='None')
    ax.plot([earth_center_xyz[0],arc_point_on_z[0]],[earth_center_xyz[1],arc_point_on_z[1]],[earth_center_xyz[2],arc_point_on_z[2]],'r-')
    ax.plot([arc_point_on_z[0],arc_point_on_vec[0]],[arc_point_on_z[1],arc_point_on_vec[1]],[arc_point_on_z[2],arc_point_on_vec[2]],'r-')
    '''
    
    ######  angle symbol wrt north pole
    #get pint on the z axis
    arc_point_on_z=get_point_on_3d_line(north_pole_xyz,earth_center_xyz,symbol_dist)
    #get ppoint on the red vector
    arc_point_on_vec=get_point_on_3d_line(north_pole_xyz,moving_point_xyz,symbol_dist)
    # plos
    ax.plot([north_pole_xyz[0],arc_point_on_z[0]],[north_pole_xyz[1],arc_point_on_z[1]],[north_pole_xyz[2],arc_point_on_z[2]],linestyle='-.', color= ROUTE_COLORS[route_abbr])
    ax.plot([arc_point_on_z[0],arc_point_on_vec[0]],[arc_point_on_z[1],arc_point_on_vec[1]],[arc_point_on_z[2],arc_point_on_vec[2]],linestyle='-.', color= ROUTE_COLORS[route_abbr])

'''' In this scrpt we efer to any pint on earth by four representaions:
1)point_geopy=geolocator.geocode(source_city_name)
2)point_latlong_tuple=(point_geopy.latitude,point_geopy.longitude)
3) point_pygeodesy=earth_model.LatLon(*point_latlong_tuple)
4)point_xyz_tuple=geodetic_to_cartesian(*point_latlong_tuple)
'''


if __name__=="__main__":
    
    for city in CITIES:
        for route_abbr, route_name in ROUTES.items():
            
            north_pole_xyz_tuple=(0,0,R)
            earth_center_xyz_tuple=(0,0,0)

            source_city_name=city
            source_geopy = geolocator.geocode(source_city_name)
            #source_latlong_tuple = (40.7128, -74.0060)  # New York City
            source_latlong_tuple=(source_geopy.latitude, source_geopy.longitude)
            mecca_latlong_tuple=KAABA

            source_geodesy=earth_model.LatLon(*source_latlong_tuple)
            mecca_geodesy=earth_model.LatLon(*mecca_latlong_tuple)

            full_distance=get_distance(source_geodesy, mecca_geodesy,route=route_abbr) #in km
            x_points, y_points, z_points=get_xyz4arc_points(source_geodesy, mecca_geodesy, n_points=100,route=route_abbr)

            source_xyz_tuple=geodetic_to_cartesian(*source_latlong_tuple)
            mecca_xyz_tuple=geodetic_to_cartesian(*mecca_latlong_tuple)

            step_distance= 1000 #in km
            distances=np.arange(0,full_distance,step_distance)
            frames=[]
            for i,moved_distance in enumerate(distances):
                fig = plt.figure(figsize=(14, 12))
                ax = fig.add_subplot(111, projection='3d')
                setup_plot(ax,R, route_name)
                plot_sphere(ax,R)
                plot_arc(ax,x_points,y_points, z_points, source_xyz_tuple,mecca_xyz_tuple, earth_center_xyz_tuple,north_pole_xyz_tuple, source_city_name)
                moving_point_xyz, bearing_to_mecca=get_xyz4moving_point(source_geodesy,mecca_geodesy, moved_distance,route=route_abbr)
                plot_moving_point(ax,earth_center_xyz_tuple,north_pole_xyz_tuple,moving_point_xyz)
                zenith_angle=np.arccos(moving_point_xyz[2]/R) #aka polar angle or theta i.e. angle wrt to z axis
                zenith_angle_opposite=R*np.sin(zenith_angle)
                
                '''
                angle_wrt_earth_center_text= f"{(180/np.pi)*zenith_angle:.0f}$^\\circ$"
                ax.text(900, 0, 1050, angle_wrt_earth_center_text, fontsize=14, ha='right')
                '''
                angle_wrt_north_pole=(180/np.pi)*np.arctan(zenith_angle_opposite/(R-moving_point_xyz[2]))
                angle_wrt_north_pole_text=f"{angle_wrt_north_pole:.0f}$^\\circ$"
                ax.text(north_pole_xyz_tuple[0]+950, north_pole_xyz_tuple[1], north_pole_xyz_tuple[2]-1200, angle_wrt_north_pole_text, fontsize=14, ha='right')

                # Adding text next to the plot in the white space
                # The coordinates (x, y) are relative to the figure (0,0) is bottom left and (1,1) is top right
                plt.figtext(0.8, 0.55, f"Distance To Mecca\n{moved_distance:.0f} Km", fontsize=12, color='black',ha='center',va='center',bbox=dict(facecolor='lightgray', edgecolor='black', boxstyle='round,pad=0.5'))
                plt.figtext(0.8, 0.45, f"Bearing To Mecca\n{bearing_to_mecca:.0f}$^\\circ$ {bearing_to_direction(bearing_to_mecca)}", fontsize=12, color='black',ha='center',va='center',bbox=dict(facecolor=ROUTE_COLORS[route_abbr], edgecolor='black', boxstyle='round,pad=0.5'))
                plt.figtext(0.3, 0.5, f"{ROUTE_COMMENTS[route_abbr]}", fontsize=12, color='black',ha='center',va='center',bbox=dict(facecolor=ROUTE_COLORS[route_abbr], edgecolor='black', boxstyle='round,pad=0.5'))
                
                # Save the current figure as an image (PNG format)
                ax.view_init(elev=30, azim=-45) # defaults 30,-60
                frame_filename = f'frame_{i}.png'
                fig.savefig(frame_filename)
                
                # Open the image and add it to the frames list
                frames.append(Image.open(frame_filename))

            # Save the frames as a GIF
            frames[0].save(f'{city}_{route_abbr}_route.gif', save_all=True, append_images=frames[1:], duration=1000, loop=0)

            # Delete the individual frame files
            for i in range(len(distances)):
                os.remove(f'frame_{i}.png')



