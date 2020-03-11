import numpy as np
import matplotlib.pyplot as plt

numPoints = 201
dt = 0.001
sigma2X = 0.005
sigma2Y = 0.005

x = np.linspace(-1, 1, numPoints)
y = np.linspace(-1, 1, numPoints)
points = np.zeros((numPoints, numPoints))

t = np.arange(0, 2 * np.pi, dt)
tx = np.sin(13 * t)
ty = np.sin(14 * t)


for i in range(len(x)):
    expX = (x[i] - tx)**2 / sigma2X
    for j in range(len(y)):
        expY = (y[j] - ty)**2 / sigma2Y
        pwr = np.exp(-0.5 * (expX + expY))
        points[j][i] = np.sum(pwr)

fig, ax = plt.subplots()
ax.imshow(points, interpolation="bilinear", origin="lower")
ax.set_axis_off()
plt.show()
