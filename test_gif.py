import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os

# Example 3D coordinates (x, y, z)
x = np.linspace(0, 10, 100)
y = np.sin(x)
z = np.cos(x)

# Create a figure and axis
fig, ax = plt.subplots()
ax.set_xlim(0, 10)
ax.set_ylim(-1.5, 1.5)

# Initialize a list to hold the image frames
frames = []

# Generate frames manually
for i in range(len(x)):
    ax.clear()  # Clear the axis for the next frame
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.5, 1.5)
    
    # Plot the point at the current frame
    ax.plot(x[i], y[i], 'bo')
    
    # Save the current figure as an image (PNG format)
    frame_filename = f'frame_{i}.png'
    fig.savefig(frame_filename)
    
    # Open the image and add it to the frames list
    frames.append(Image.open(frame_filename))

# Save the frames as a GIF
frames[0].save('moving_point.gif', save_all=True, append_images=frames[1:], duration=100, loop=0)

# Delete the individual frame files
for i in range(len(x)):
    os.remove(f'frame_{i}.png')

plt.show()
