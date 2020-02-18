import wx
import wx.glcanvas as wxcanvas
import numpy as np
from OpenGL import GL, GLU
from collections import deque
from math import floor


class Lissajous():
    """Lissajous
    """

    def __init__(self, xFreq, yFreq, phaseShift):
        """Initialise"""

        self.width = 1
        self.height = 1
        self.xScale = 2 * np.pi / self.width
        self.yScale = 2 * np.pi / self.height
        self.x = 0
        self.y = self.height / 2
        self.xFreq = xFreq
        self.yFreq = yFreq
        self.delta = phaseShift

    def initialise(self, width=1, height=1):
        """"""

        self.width = width
        self.height = height
        self.xScale = 2 * np.pi / self.width
        self.yScale = 2 * np.pi / self.height
        self.y = self.height / 2

    def setXFreq(self, f):
        """Set x frequency"""
        self.xFreq = f

    def setYFreq(self, f):
        """Set y frequency"""
        self.yFreq = f

    def updatePattern(self, dt):
        """"""

        self.x = np.sin(self.xFreq * dt * self.xScale)
        self.y = np.sin(self.yFreq * dt * self.yScale + self.delta)

class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    Parameters
    ----------
    parent: parent widget - the signal panel
    init: bool specifying if canvas has been initialised
    context: the GL context

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.
    """

    def __init__(self, parent, lis):
        """Initialise canvas properties and useful variables."""

        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])

        self.parent = parent
        self.lissajous = lis
        self.counter = 0
        self.n = 1000
        self.timer = wx.Timer(self)
        self.points = np.empty((self.n,2))
        self.colours = np.linspace((0,0,0), (1,1,1), num=self.n)

        # Set the context to the canvas
        self.init = False
        self.context = wxcanvas.GLContext(self)

        # Bind events to widgets
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_TIMER, self.on_timer)

    def init_gl(self):
        """Configure and initialise the 2D OpenGL context."""

        self.SetCurrent(self.context)
        self.counter = self.n
        size = self.GetClientSize()

        for i in range (self.n):
            self.lissajous.updatePattern(i)
            self.points[i] = [self.lissajous.x * size.width * 0.75,
                              self.lissajous.y * size.height * 0.75]

        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)
        GL.glColorPointer(3, GL.GL_FLOAT, 0, self.colours)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-size.width, size.width, -size.height, size.height, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        self.timer.Start(40)

    def render(self):
        """Handle all drawing operations."""

        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Draw
        GL.glDrawArrays(GL.GL_LINE_STRIP, 0, self.n)

        GL.glFlush()
        self.SwapBuffers()

    def on_paint(self, event):
        """Handle the paint event."""

        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True
        self.render()

    def on_timer(self, event):
        """"""

        self.SetCurrent(self.context)
        self.counter += 1
        self.lissajous.updatePattern(self.counter)

        size = self.GetClientSize()
        self.points = np.roll(self.points, (-1, -1))
        self.points[-1] = [self.lissajous.x * size.width * 0.75,
                           self.lissajous.y * size.height * 0.75]
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)
        self.Refresh()


class Control(wx.Panel):
    """"""

    def __init__(self, parent, lis, glcan):
        """"""

        super().__init__(parent)

        self.lissajous = lis
        self.canvas = glcan
        self._delta = np.linspace(0, 2 * np.pi, num=100)

        self.xSlider = wx.Slider(self, value=self.lissajous.xFreq,
                                 minValue=1, maxValue=20,
                                 style=wx.SL_AUTOTICKS)

        self.ySlider = wx.Slider(self, value=self.lissajous.yFreq,
                                 minValue=1, maxValue=20,
                                 style=wx.SL_VERTICAL|wx.SL_AUTOTICKS)

        self.deltaSlider = wx.Slider(self, minValue=1, maxValue=100)
        self.resetButton = wx.Button(self)

        self.resetButton.SetLabel("Reset")

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.Add(self.xSlider, 1, wx.EXPAND)
        self.box.Add(self.ySlider, 1, wx.EXPAND)
        self.box.Add(self.deltaSlider, 1, wx.EXPAND)
        self.box.Add(self.resetButton)
        self.SetSizer(self.box)

        self.xSlider.Bind(wx.EVT_SLIDER, self.on_x_slider)
        self.ySlider.Bind(wx.EVT_SLIDER, self.on_y_slider)
        self.deltaSlider.Bind(wx.EVT_SLIDER, self.on_delta_slider)
        self.resetButton.Bind(wx.EVT_BUTTON, self.on_button)

    def on_x_slider(self, event):
        """"""
        self.lissajous.xFreq = self.xSlider.GetValue()
        self.canvas.init_gl()

    def on_y_slider(self, event):
        """"""
        self.lissajous.yFreq = self.ySlider.GetValue()
        self.canvas.init_gl()

    def on_delta_slider(self, event):
        """"""
        self.lissajous.delta = self._delta[self.deltaSlider.GetValue()-1]
        self.canvas.init_gl()

    def on_button(self, event):
        """"""
        self.canvas.init_gl()



class Gui(wx.Frame):
    """Configure the main window.

    Parameters
    ----------
    title: title of the window.
    """

    def __init__(self, title, lis, width=600, height=600):
        """Initialise tabs."""

        super().__init__(parent=None, title=title, size=(width, height),
                         style=(wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)))
        self.SetSizeHints(600, 600)  # Controls minimum parent window size

        self.lissajous = lis
        self.lissajous.initialise(width, height)
        self.canvas = MyGLCanvas(self, self.lissajous)
        self.control = Control(self, self.lissajous, self.canvas)

        # Define layout
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.canvas, 1, wx.EXPAND)
        box.Add(self.control)
        self.SetSizer(box)


def main():
    lis = Lissajous(1, 1, 0)
    app = wx.App()
    gui = Gui("Lissajous", lis)
    gui.Show(True)
    app.MainLoop()

if __name__ == "__main__":
    main()
