"""
A simple script to plot a Lissajous figure.
"""

# Import required modules
import numpy as np               # Numeric library
import matplotlib.pyplot as plt  # Plotting module

# Initialise an array with values of t
# Results in 1000 evenly spaced points in the interval [0, 2 * pi)
t = np.linspace(0, 2 * np.pi, 1000, endpoint=false)

# Calculate the Lissajous figure
x = np.sin(t)
y = np.sin(2 * t)

# Plot the Lissajous figure
plt.plot(x, y)
plt.show()
