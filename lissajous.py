import wx
import wx.glcanvas as wxcanvas
import wx.lib.newevent as wxevt
import numpy as np
from OpenGL import GL


FrequencySliderEvent, EVT_FSLIDER = wxevt.NewEvent()
PhaseShiftSliderEvent, EVT_PSLIDER = wxevt.NewEvent()
AnimationControlEvent, EVT_ACONTROL = wxevt.NewEvent()


class Lissajous():
    """Lissajous
    """

    def __init__(self, xFreq, yFreq, phaseShift):
        """Initialise"""

        self.x = 0
        self.y = 0
        self.xFreq = xFreq
        self.yFreq = yFreq
        self.delta = phaseShift

    def updatePattern(self, dt):
        """"""

        self.x = np.sin(self.xFreq * dt)
        self.y = np.sin(self.yFreq * dt + self.delta)


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    Parameters
    ----------
    parent: parent widget - the signal panel
    init: bool specifying if canvas has been initialised
    context: the GL context

    Public methods
    --------------
    initGl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    onPaint(self, event): Handles the paint event.
    """

    def __init__(self, parent, lis, initSize=(500, 500)):
        """Initialise canvas properties and useful variables."""

        super().__init__(parent, -1,
                         size=initSize,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])

        self.parent = parent
        self.lissajous = lis
        self.numPoints = 0
        self.timer = wx.Timer(self)
        self.timerStep = 10

        self.cycles = 10
        self.numPointsFrozen = 1000 * self.cycles + 1
        self.points = np.zeros((self.numPointsFrozen, 2))
        self.colours = np.zeros((self.numPointsFrozen, 3))

        self.numPointsToAnimate = 1000
        self.animationTimestep = 2 * np.pi / (1000)
        self.currentTimestep = 0

        self.bFrozen = True

        # Set the context to the canvas
        self.init = False
        self.context = wxcanvas.GLContext(self)

        # Bind events to widgets
        self.Bind(wx.EVT_PAINT, self.onPaint)

    def initGl(self):
        """Configure and initialise the 2D OpenGL context."""

        self.SetCurrent(self.context)
        size = self.GetClientSize()

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-size.width, size.width, -size.height, size.height, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        if self.bFrozen:
            self.initGlFrozen()
        else:
            self.initGlAnimate()

    def initGlFrozen(self):
        """Configure and initialise the 2D OpenGL context."""

        self.SetCurrent(self.context)
        size = self.GetClientSize()
        self.points = np.zeros((self.numPointsFrozen, 2))
        self.colours = np.ones((self.numPointsFrozen, 3))

        count = 0
        for i in np.linspace(0, 2 * self.cycles * np.pi, self.numPointsFrozen):
            self.lissajous.updatePattern(i)
            self.points[count] = [self.lissajous.x * size.width * 0.75,
                                  self.lissajous.y * size.height * 0.75]
            count += 1

        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)
        GL.glColorPointer(3, GL.GL_FLOAT, 0, self.colours)
        self.numPoints = self.numPointsFrozen

        self.init = True
        self.Refresh()

    def initGlAnimate(self):
        """Configure and initialise the 2D OpenGL context."""

        self.SetCurrent(self.context)
        size = self.GetClientSize()
        self.points = np.zeros((1, 2))
        self.colours = np.ones((1, 3))
        self.currentTimestep = self.animationTimestep

        self.lissajous.updatePattern(self.currentTimestep)
        self.points[0] = [self.lissajous.x * size.width * 0.75,
                          self.lissajous.y * size.height * 0.75]

        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)
        GL.glColorPointer(3, GL.GL_FLOAT, 0, self.colours)
        self.numPoints = 1

        self.init = True

        self.timer.Start(self.timerStep)
        self.Bind(wx.EVT_TIMER, self.onInitialTimer)

    def onPaint(self, event):
        """Handle the paint event."""

        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.initGl()

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Draw
        GL.glDrawArrays(GL.GL_LINE_STRIP, 0, self.numPoints)

        GL.glFlush()
        self.SwapBuffers()

    def onInitialTimer(self, event):
        """"""

        self.SetCurrent(self.context)
        size = self.GetClientSize()
        numStepsSoFar = len(self.points)

        if numStepsSoFar < self.numPointsToAnimate:
            numStepsSoFar += 1
            self.currentTimestep += self.animationTimestep

            self.lissajous.updatePattern(self.currentTimestep)
            self.points = np.append(self.points,
                                    [[self.lissajous.x * size.width * 0.75,
                                      self.lissajous.y * size.height * 0.75]],
                                    0)
            self.colours = np.linspace((0, 0, 0), (1, 1, 1), numStepsSoFar)

            GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)
            GL.glColorPointer(3, GL.GL_FLOAT, 0, self.colours)
            self.numPoints = numStepsSoFar

            self.Refresh()

        else:
            self.timer.Stop()
            self.Unbind(wx.EVT_TIMER)

            if numStepsSoFar > self.numPointsToAnimate:
                self.points = self.points[:self.numPointsToAnimate]

            self.colours = np.linspace((0, 0, 0), (1, 1, 1),
                                       self.numPointsToAnimate)
            GL.glColorPointer(3, GL.GL_FLOAT, 0, self.colours)
            self.numPoints = self.numPointsToAnimate

            self.timer.Start(self.timerStep)
            self.Bind(wx.EVT_TIMER, self.onTimer)

    def onTimer(self, event):
        """"""

        self.SetCurrent(self.context)
        size = self.GetClientSize()

        self.currentTimestep += self.animationTimestep
        self.lissajous.updatePattern(self.currentTimestep)

        self.points = np.roll(self.points, (-1, -1))
        self.points[-1] = [self.lissajous.x * size.width * 0.75,
                           self.lissajous.y * size.height * 0.75]
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)

        self.Refresh()

    def stopAnimate(self):
        """"""
        self.timer.Stop()
        self.Unbind(wx.EVT_TIMER)


class FrequencySlider(wx.Panel):
    """"""

    def __init__(self, parent, labelText, initValue=1,
                 initStyle=wx.SL_HORIZONTAL, initMin=1, initMax=30):
        """"""

        super().__init__(parent)
        self.value = initValue

        self.slider = wx.Slider(self, value=initValue, style=initStyle,
                                minValue=initMin * 10, maxValue=initMax * 10)
        self.spinCtrl = wx.SpinCtrlDouble(self, initial=initValue,
                                          min=initMin, max=initMax, inc=0.1)
        self.label = wx.StaticText(self, label=labelText)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.slider, 1, wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)
        self.vbox.AddSpacer(10)
        self.spinCtrl.SetSize(self.slider.GetSize())
        self.vbox.Add(self.spinCtrl, 1,
                      wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.AddSpacer(5)
        self.hbox.Add(self.label, 1, wx.ALIGN_CENTRE_VERTICAL)
        self.hbox.AddSpacer(20)
        self.hbox.Add(self.vbox)
        self.SetSizer(self.hbox)

        self.slider.Bind(wx.EVT_SLIDER, self.onSlider)
        self.spinCtrl.Bind(wx.EVT_SPINCTRLDOUBLE, self.onSpin)

    def onSlider(self, event):
        """"""

        self.value = self.slider.GetValue() / 10
        self.spinCtrl.SetValue(self.value)
        wx.PostEvent(self, FrequencySliderEvent())

    def onSpin(self, event):
        """"""

        self.value = self.spinCtrl.GetValue()
        self.slider.SetValue(int(self.value * 10))
        wx.PostEvent(self, FrequencySliderEvent())


class PhaseShiftSlider(wx.Panel):
    """"""

    def __init__(self, parent):
        """"""

        super().__init__(parent)
        self.slider = wx.Slider(self, value=0, minValue=0,
                                maxValue=24, style=wx.SL_AUTOTICKS)
        self.value = 0
        self.valueLabel = wx.StaticText(self, label="0 rad")
        self.labels = [str(i) + "\u03c0 / 12 rad" for i in range(25)]
        self.labels[0] = "0 rad"
        self.labels[12] = "\u03c0 rad"
        self.labels[24] = "2\u03c0 rad"

        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.box.AddSpacer(5)
        self.box.Add(self.slider)
        self.box.AddSpacer(10)
        self.box.Add(self.valueLabel)
        self.SetSizer(self.box)

        self.slider.Bind(wx.EVT_SLIDER, self.onSlider)

    def onSlider(self, event):
        """"""

        v = self.slider.GetValue()
        self.value = np.pi * v / 12
        self.valueLabel.SetLabel(self.labels[v])
        wx.PostEvent(self, PhaseShiftSliderEvent())


class AnimationControls(wx.Panel):
    """"""

    def __init__(self, parent):
        """"""

        super().__init__(parent)
        self.bReset = False
        self.bAnimate = False
        self.animateButton = wx.Button(self, label="Turn animation on ")
        self.resetButton = wx.Button(self, label="Reset")
        self.resetButton.Disable()

        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.box.AddSpacer(5)
        self.box.Add(self.animateButton)
        self.box.AddSpacer(20)
        self.box.Add(self.resetButton)
        self.box.AddSpacer(5)
        self.SetSizer(self.box)

        self.animateButton.Bind(wx.EVT_BUTTON, self.onAnimateButton)
        self.resetButton.Bind(wx.EVT_BUTTON, self.onResetButton)

    def onAnimateButton(self, event):
        """"""

        if self.bAnimate:
            self.bAnimate = False
            self.animateButton.SetLabel("Turn animation on ")
            self.resetButton.Disable()

        else:
            self.bAnimate = True
            self.animateButton.SetLabel("Turn animation off")
            self.resetButton.Enable()

        wx.PostEvent(self, AnimationControlEvent())

    def onResetButton(self, event):
        """"""

        self.bReset = True
        wx.PostEvent(self, AnimationControlEvent())


class Control(wx.Panel):
    """"""

    def __init__(self, parent, lis, glcan):
        """"""

        super().__init__(parent)

        self.lissajous = lis
        self.canvas = glcan

        self.xSlider = FrequencySlider(self, "x frequency:",
                                       initValue=self.lissajous.xFreq)
        self.ySlider = FrequencySlider(self, "y frequency:",
                                       initValue=self.lissajous.yFreq)

        self.freqControlBox = wx.StaticBoxSizer(wx.VERTICAL, self,
                                                "Frequency Controls")
        self.freqControlBox.AddSpacer(10)
        self.freqControlBox.Add(self.xSlider)
        self.freqControlBox.AddSpacer(30)
        self.freqControlBox.Add(self.ySlider)
        self.freqControlBox.AddSpacer(10)

        self.deltaSlider = PhaseShiftSlider(self)
        self.phaseControlBox = wx.StaticBoxSizer(wx.VERTICAL, self,
                                                 "Phase shift control")
        self.phaseControlBox.AddSpacer(10)
        self.phaseControlBox.Add(self.deltaSlider, 0, wx.EXPAND)
        self.phaseControlBox.AddSpacer(10)

        self.animationButtons = AnimationControls(self)
        self.animationControlBox = wx.StaticBoxSizer(wx.VERTICAL, self,
                                                     "Animation controls")
        self.animationControlBox.AddSpacer(10)
        self.animationControlBox.Add(self.animationButtons)
        self.animationControlBox.AddSpacer(10)

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.AddStretchSpacer(2)
        self.box.Add(self.freqControlBox, 0, wx.EXPAND)
        self.box.AddStretchSpacer(1)
        self.box.Add(self.phaseControlBox, 0, wx.EXPAND)
        self.box.AddStretchSpacer(1)
        self.box.Add(self.animationControlBox, 0, wx.EXPAND)
        self.box.AddStretchSpacer(2)
        self.SetSizer(self.box)

        self.xSlider.Bind(EVT_FSLIDER, self.onXSlider)
        self.ySlider.Bind(EVT_FSLIDER, self.onYSlider)
        self.deltaSlider.Bind(EVT_PSLIDER, self.onDeltaSlider)
        self.animationButtons.Bind(EVT_ACONTROL, self.onAnimationButtons)

    def onXSlider(self, event):
        """"""
        self.lissajous.xFreq = self.xSlider.value
        self.canvas.init = False
        self.canvas.Refresh()

    def onYSlider(self, event):
        """"""
        self.lissajous.yFreq = self.ySlider.value
        self.canvas.init = False
        self.canvas.Refresh()

    def onDeltaSlider(self, event):
        """"""
        self.lissajous.delta = self.deltaSlider.value
        self.canvas.init = False
        self.canvas.Refresh()

    def onAnimationButtons(self, event):
        """"""
        self.canvas.stopAnimate()

        if self.animationButtons.bReset:
            self.animationButtons.bReset = False

        else:
            self.canvas.bFrozen = not self.animationButtons.bAnimate

        self.canvas.init = False
        self.canvas.Refresh()


class Gui(wx.Frame):
    """Configure the main window.

    Parameters
    ----------
    title: title of the window.
    """

    def __init__(self, title, lis):
        """Initialise tabs."""

        super().__init__(parent=None,
                         title=title,
                         style=(wx.DEFAULT_FRAME_STYLE &
                                ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)))

        self.lissajous = lis
        self.canvas = MyGLCanvas(self, self.lissajous)
        self.control = Control(self, self.lissajous, self.canvas)

        # Define layout
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.canvas, 0)
        box.Add(self.control, 0, wx.EXPAND)
        self.SetSizerAndFit(box)


def main():
    lis = Lissajous(1, 1, 0)
    app = wx.App()
    gui = Gui("Lissajous", lis)
    gui.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    main()
