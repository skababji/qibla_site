import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches

# Define the points for the two lines
line1_point1 = np.array([0, 0])
line1_point2 = np.array([1, 2])

line2_point1 = np.array([0, 0])
line2_point2 = np.array([2, 1])

# Plot the lines
plt.plot([line1_point1[0], line1_point2[0]], [line1_point1[1], line1_point2[1]], 'b-')
plt.plot([line2_point1[0], line2_point2[0]], [line2_point1[1], line2_point2[1]], 'r-')

# Calculate the angle between the lines
v1 = line1_point2 - line1_point1
v2 = line2_point2 - line2_point1

cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
angle = np.arccos(cos_theta)
angle_degrees = np.degrees(angle)

# Draw the arc
arc_radius = 0.5
arc = patches.Arc((0, 0), 2*arc_radius, 2*arc_radius, angle=0, theta1=0, theta2=angle_degrees, edgecolor='k')
plt.gca().add_patch(arc)

# Add the angle label
angle_label = f'{angle_degrees:.2f}°'
plt.text(arc_radius, arc_radius, angle_label, fontsize=12, ha='center')

# Set the aspect of the plot to be equal
plt.gca().set_aspect('equal', adjustable='box')

# Set the limits of the plot
plt.xlim(-1, 3)
plt.ylim(-1, 3)

# Show the plot
plt.show()
