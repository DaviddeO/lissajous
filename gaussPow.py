"""
Find and display the energy distribution of a Lissajous laser scanner.

The trapezium rule is used to numerically integrate the power distribution
of a laser scanner. In this example the distribution is a 2D Gaussian:

         p(x,y,t) = exp(-0.5( ((x - tx)^2)/sx + ((y - ty)^2)/sy )),

where tx and ty are the parametric equations for the Lissajous figure,
and sx and sy are widths of the laser spot in the x an y directions.
To find the energy distribution as a function of position (x,y), the above
power distribution must be integrated with respect to t.
"""

import numpy as np
import matplotlib.pyplot as plt

# Define constants to use
numPoints = 201  # The resulting image will be of size numPoints x numPoints
dt = 0.001       # The step size to use in the numerical integration
sigma2X = 0.005  # The spot-size in the x-direction of the laser
sigma2Y = 0.005  # The spot-size in the y-direction of the laser

# Create the image array
points = np.zeros((numPoints, numPoints))

# Initialise the arrays for values of x, y and t
x = np.linspace(-1, 1, numPoints)
y = np.linspace(-1, 1, numPoints)
t = np.arange(0, 2 * np.pi, dt)

# Calculate the Lissajous figure
tx = np.sin(t)
ty = np.sin(t + np.pi / 2)

# Run the numerical integration to find the energy distribution
for i in range(len(x)):
    expX = (x[i] - tx)**2 / sigma2X
    for j in range(len(y)):
        expY = (y[j] - ty)**2 / sigma2Y

        # Calculate the power distribution at this particular position (x,y)
        # for all values of t
        pwr = np.exp(-0.5 * (expX + expY))

        # Carry out the trapezium rule
        points[j][i] = dt * (np.sum(pwr[1:-1]) + (pwr[0] + pwr[-1]) / 2)

# Plot the resulting energy distribution
fig, ax = plt.subplots()
ax.imshow(points, interpolation="bilinear", origin="lower")  # Plot
ax.set_axis_off()
plt.show()
