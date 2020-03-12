"""
Lissajous curve sketcher (using Matplotlib.pyplot).

This script plots a Lissajous figure and provides a graphical user
interface to allow the user to vary the parameters in the Lissajous
parametric equations.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


# Create the figure and a set of axes for the the plot
fig, ax = plt.subplots()
plt.subplots_adjust(left=0.25, bottom=0.25)

# Initialise the array for values of t
t = np.linspace(0, 2 * np.pi, 1000)


# Define the functions x(t) and y(t)
def x(omegaX, t):
    """Calculate the Lissajous x coordinate."""
    return np.sin(omegaX * t)


def y(omegaY, phi, t):
    """Calculate the Lissajous y coordinate."""
    return np.sin(omegaY * t + phi)


# Initial plot
graph, = plt.plot(x(1, t), y(1, 0, t))

# Lay out the plot and the sliders used to modify the plot
axOmegaX = plt.axes([0.25, 0.15, 0.65, 0.03])
axOmegaY = plt.axes([0.25, 0.1, 0.65, 0.03])
axDelta = plt.axes([0.25, 0.05, 0.65, 0.03])
axNum = plt.axes([0.25, 0, 0.65, 0.03])

# Create the sliders
sOmegaX = Slider(axOmegaX, 'OmegaX', 1, 30.0,
                 valinit=1, valstep=0.1)
sOmegaY = Slider(axOmegaY, 'OmegaY', 1, 30.0,
                 valinit=1, valstep=0.1)
sDelta = Slider(axDelta, 'Phase shift', 0, 2 * np.pi,
                valinit=0, valstep=np.pi / 12)
sNum = Slider(axNum, 'Number of cycles', 0.5, 10,
              valinit=1, valstep=0.5)


# Define the update functions
# which are called every time the user uses one of the sliders
def update(val):
    """Update the values to be plotted and replot figure."""
    # Get the values from the sliders
    omegaX = sOmegaX.val
    omegaY = sOmegaY.val
    phi = sDelta.val

    # Update the data used for plotting
    graph.set_data(x(omegaX, t), y(omegaY, phi, t))

    # Re-plot the data
    fig.canvas.draw_idle()


def updateT(val):
    """Update the values to be plotted and replot figure."""
    # Make sure we update the t we defined earlier
    global t

    # Get the values from the sliders
    omegaX = sOmegaX.val
    omegaY = sOmegaY.val
    phi = sDelta.val
    num = sNum.val

    # Update t
    t = np.linspace(0, 2 * num * np.pi, int(1000 * num))

    # Update the data used for plotting
    graph.set_data(x(omegaX, t), y(omegaY, phi, t))

    # Re-plot the data
    fig.canvas.draw_idle()


# Associate the update functions with the sliders
sOmegaX.on_changed(update)
sOmegaY.on_changed(update)
sDelta.on_changed(update)
sNum.on_changed(updateT)

# Display everything
plt.show()
