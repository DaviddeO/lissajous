"""Plot a 2D Gaussian distribution."""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # 3D plotting tools

# Define the variances in the x and y directions
sigma2X = 1
sigma2Y = 1

# Create x and y arrays
x = np.linspace(-4, 4, 101)
y = np.linspace(-4, 4, 101)

# Create a meshgrid
# This enables us to calculate the Gaussian function over a grid of x,y values
X, Y = np.meshgrid(x, y)

# Calcuate the Gaussian function
Z = np.exp(-0.5 * ((X**2 / sigma2X) + (Y**2 / sigma2Y)))

# Set up the 3D axis to plot
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

# Plot the Gaussian and display
ax.plot_surface(X, Y, Z)
plt.show()
