"""
Lissajous curve sketcher.

An application which draws out the Lissajous curve
given user-specified settings

Classes
-------
Lissajous: Handles the Lissajous operations
MyGLCanvas: Handles the drawing operations
FrequencySlider: Implements the freq controls
PhaseShiftSlider: Implements the phaseshift controls
AnimationControls: Implements the animation controls
Control: Provides the user controls
Gui: The main application window
"""

import wx
import wx.glcanvas as wxcanvas
import wx.lib.newevent as wxevt
import numpy as np
from OpenGL import GL


FrequencySliderEvent, EVT_FSLIDER = wxevt.NewEvent()
PhaseShiftSliderEvent, EVT_PSLIDER = wxevt.NewEvent()
AnimationControlEvent, EVT_ACONTROL = wxevt.NewEvent()


class Lissajous():
    """
    Handle the Lissajous variables and operations.

    Parameters
    ----------
    xFreq: Sets the initial x angular frequency
    yFreq: Sets the initial y angular frequency
    phaseShift: Sets the initial phaseshift

    Variables
    ---------
    x: x value after the latest Lissajous update given by
       sin(xFreq * t)
    y: y value after the latest Lissajous update given by
       sin(yFreq * t + delta)
    xFreq: The x angular frequency
    yFreq: The y angular frequency
    delta: The phaseshift, in radians

    Methods
    -------
    updatePattern(dt): Perform an update for the x and y values of the
                       Lissajous curve at the given value of dt
    """

    def __init__(self, xFreq, yFreq, phaseShift):
        """Initialise the class."""
        self.x = 0
        self.y = 0
        self.xFreq = xFreq
        self.yFreq = yFreq
        self.delta = phaseShift

    def updatePattern(self, dt):
        """Update x and y values of the Lissajous curve at the given dt."""
        self.x = np.sin(self.xFreq * dt)
        self.y = np.sin(self.yFreq * dt + self.delta)


class MyGLCanvas(wxcanvas.GLCanvas):
    """
    Handle all drawing operations.

    Parameters
    ----------
    parent: Parent widget - the Gui frame
    lis: An instance of the Lissajous class
    size_: Sets the size of the canvas

    Variables
    ----------
    parent: Parent widget - the Gui frame
    lissajous: An instance of the Lissajous class
    numPoints: Number of points to draw on the Glcanvas
    timer: The timer used to update the animation of the Lissajous curve
    timerStep: Specifies how often to update the animation; in milliseconds
    scale: Scaling factor for rendering points
    cycles: Number of cycles for which to draw the Lissajous curve when
            not animating
    points: Numpy array holding the coordinates for all the points of the
            Lissajous curve to be rendered
    colours: Numpy array holding the colour of each point to be rendered
    numPointsFrozen: Number of points used to render Lissajous curve when
                     not animating
    numPointsToAnimate: Number of points to render when animating
                        the Lissajous curve
    animationTimestep: The time resolution at which to evaluate the
                       Lissajous curve when animating
    currentTimestep: The current timestep at which to evaluate the
                     Lissajous curve when animating
    bFrozen: bool specifying whether in animating or frozen mode
    init: bool specifying if canvas has been initialised
    context: The GL context

    Methods
    --------------
    initGl(self): Configures the OpenGL context and modelview matrix
    initGlFrozen(self): Sets up the points and colours arrays for rendering
                        in frozen mode
    initGlAnimate(self): Sets up the points and colours arrays for animating
    onPaint(self, event): Handles the paint event and drawing operations
    onInitialTimer(self, event): Start animation drawing from 0 to
                                 numPointsToAnimate points
    onTimer(self, event): Proceed with animation
    stopAnimate(self): Stop the animation
    """

    def __init__(self, parent, lis, size_=(500, 500)):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         size=size_,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])

        self.parent = parent
        self.lissajous = lis
        self.numPoints = 0
        self.timer = wx.Timer(self)
        self.timerStep = 10
        self.scale = 0.75

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
        """Configure the OpenGL context and modelview matrix."""
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
        """Set up points and colours arrays for rendering in frozen mode."""
        self.SetCurrent(self.context)
        size = self.GetClientSize()
        self.points = np.zeros((self.numPointsFrozen, 2))
        self.colours = np.ones((self.numPointsFrozen, 3))

        count = 0
        for i in np.linspace(0, 2 * self.cycles * np.pi, self.numPointsFrozen):
            self.lissajous.updatePattern(i)
            self.points[count] = [self.lissajous.x * size.width * self.scale,
                                  self.lissajous.y * size.height * self.scale]
            count += 1

        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)
        GL.glColorPointer(3, GL.GL_FLOAT, 0, self.colours)
        self.numPoints = self.numPointsFrozen

        self.init = True
        self.Refresh()

    def initGlAnimate(self):
        """Set up the points and colours arrays for animating."""
        self.SetCurrent(self.context)
        size = self.GetClientSize()
        self.points = np.zeros((1, 2))
        self.colours = np.ones((1, 3))
        self.currentTimestep = self.animationTimestep

        self.lissajous.updatePattern(self.currentTimestep)
        self.points[0] = [self.lissajous.x * size.width * self.scale,
                          self.lissajous.y * size.height * self.scale]

        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)
        GL.glColorPointer(3, GL.GL_FLOAT, 0, self.colours)
        self.numPoints = 1

        self.init = True

        self.timer.Start(self.timerStep)
        self.Bind(wx.EVT_TIMER, self.onInitialTimer)

    def onPaint(self, event):
        """Handle the paint event and drawing operations."""
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
        """Start animation drawing from 0 to numPointsToAnimate points."""
        self.SetCurrent(self.context)
        size = self.GetClientSize()
        wScale = size.width * self.scale
        hScale = size.height * self.scale
        numStepsSoFar = len(self.points)

        if numStepsSoFar < self.numPointsToAnimate:
            numStepsSoFar += 1
            self.currentTimestep += self.animationTimestep

            self.lissajous.updatePattern(self.currentTimestep)
            self.points = np.append(self.points,
                                    [[self.lissajous.x * wScale,
                                     self.lissajous.y * hScale]],
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
        """Proceed with animation."""
        self.SetCurrent(self.context)
        size = self.GetClientSize()

        self.currentTimestep += self.animationTimestep
        self.lissajous.updatePattern(self.currentTimestep)

        self.points = np.roll(self.points, (-1, -1))
        self.points[-1] = [self.lissajous.x * size.width * self.scale,
                           self.lissajous.y * size.height * self.scale]
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, self.points)

        self.Refresh()

    def stopAnimate(self):
        """Stop the animation."""
        self.timer.Stop()
        self.Unbind(wx.EVT_TIMER)


class FrequencySlider(wx.Panel):
    """
    Implement frequency control for Lissajous curve.

    Parameters
    ----------
    parent: Parent widget - the control panel
    label_: Label for the panel
    value_: Initial value for the frequency
    style_: The panel's style
    min_: The lower limit of the allowed frequency range
    max_: The upper limit of the allowed frequency range

    Variables
    ---------
    value: The desired frequency value
    slider: The wx.Slider object to allow the user to specify the frequency
    spinCtrl: The wx.SpinCtrlDouble object to allow the user to specify the
              frequency
    label: Label for the panel
    vbox: The layout sizer for slider and spinCtrl
    hbox: The layout sizer for the panel

    Methods
    -------
    onSlider(self, event): Handles the slider event
    onSpin(self, event): Handles the spin event
    """

    def __init__(self, parent, label_, value_=1,
                 style_=wx.SL_HORIZONTAL, min_=1, max_=30):
        """Initialise and lay out the panel."""
        super().__init__(parent)
        self.value = value_

        self.slider = wx.Slider(self, value=value_, style=style_,
                                minValue=min_ * 10, maxValue=max_ * 10)
        self.spinCtrl = wx.SpinCtrlDouble(self, initial=value_,
                                          min=min_, max=max_, inc=0.1)
        self.label = wx.StaticText(self, label=label_)

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
        """Handle the slider event."""
        self.value = self.slider.GetValue() / 10
        self.spinCtrl.SetValue(self.value)
        wx.PostEvent(self, FrequencySliderEvent())

    def onSpin(self, event):
        """Handle the spin event."""
        self.value = self.spinCtrl.GetValue()
        self.slider.SetValue(int(self.value * 10))
        wx.PostEvent(self, FrequencySliderEvent())


class PhaseShiftSlider(wx.Panel):
    """
    Implement phase shift control for the Lissajous curve.

    Parameters
    ----------
    parent: Parent widget - the control panel

    Variables
    ---------
    slider: The wx.Slider object to allow the user to specify the phaseshift
    value: The phaseshift amount
    valueLabel: The text displaying the phaseshift amount
    labels: List holding the strings for valueLabel
    box: The layout sizer for the panel

    Methods
    -------
    onSlider(self, event): Handles the slider event
    """

    def __init__(self, parent):
        """Initialise and lay out the panel."""
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
        """"Handle the slider event."""
        v = self.slider.GetValue()
        self.value = np.pi * v / 12
        self.valueLabel.SetLabel(self.labels[v])
        wx.PostEvent(self, PhaseShiftSliderEvent())


class AnimationControls(wx.Panel):
    """
    Implement animation controls; to stop, start and reset the animation.

    Parameters
    ----------
    parent: Parent widget - the control panel

    Variables
    ---------
    bReset: bool specifying whether the animation should be reset
    bAnimate: bool specifying whether in animation or frozen mode
    animateButton: The wx.Button object allowing the user to turn
                   the animation mode on/off
    resetButton: The wx.Button object allowing the user to reset
                 the animation
    box: The layout sizer for the panel

    Methods
    -------
    onAnimateButton(self, event): Handles the animation button event
    onResetButton(self, event): Handles the reset button event
    """

    def __init__(self, parent):
        """Initialise and lay out the panel."""
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
        """Handle the animation button event."""
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
        """Handle the reset button event."""
        self.bReset = True
        wx.PostEvent(self, AnimationControlEvent())


class Control(wx.Panel):
    """
    Implement the control panel.

    Parameters
    ----------
    parent: Parent widget - the Gui frame
    lis: An instance of the Lissajous class
    glcan: An instance of the MyGLCanvas class

    Variables
    ---------
    lissajous: An instance of the Lissajous class
    canvas: An instance of the MyGLCanvas class
    xSlider: The controls for the x frequency
    ySlider: The controls for the y frequency
    freqControlBox: Layout sizer for the frequency controls
    deltaSlider: The slider control for the phaseshift
    phaseControlBox: Layout sizer for the phase control
    animationButtons: The controls for the animation
    animationControlBox: Layout sizer for the animation controls
    box: The layout sizer for the panel

    Methods
    -------
    onXSlider(self, event): Handles the event the x frequency has been changed
    onYSlider(self, event): Handles the event the y frequency has been changed
    onDeltaSlider(self, event): Handles the event the phaseshift has been
                                changed
    onAnimationButtons(self, event): Handles the event an animation control
                                     button has been clicked
    """

    def __init__(self, parent, lis, glcan):
        """Initialise and lay out the panel."""
        super().__init__(parent)

        self.lissajous = lis
        self.canvas = glcan

        self.xSlider = FrequencySlider(self, "x frequency:",
                                       value_=self.lissajous.xFreq)
        self.ySlider = FrequencySlider(self, "y frequency:",
                                       value_=self.lissajous.yFreq)

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
        """Handle the event the x frequency has been changed."""
        self.lissajous.xFreq = self.xSlider.value
        self.canvas.init = False
        self.canvas.Refresh()

    def onYSlider(self, event):
        """Handle the event the y frequency has been changed."""
        self.lissajous.yFreq = self.ySlider.value
        self.canvas.init = False
        self.canvas.Refresh()

    def onDeltaSlider(self, event):
        """Handle the event the phaseshift has been changed."""
        self.lissajous.delta = self.deltaSlider.value
        self.canvas.init = False
        self.canvas.Refresh()

    def onAnimationButtons(self, event):
        """Handle the event an animation control button has been clicked."""
        self.canvas.stopAnimate()

        if self.animationButtons.bReset:
            self.animationButtons.bReset = False

        else:
            self.canvas.bFrozen = not self.animationButtons.bAnimate

        self.canvas.init = False
        self.canvas.Refresh()


class Gui(wx.Frame):
    """The main window.

    Parameters
    ----------
    title: Title of the window
    lis: An instance of the Lissajous class

    Variables
    ---------
    lissajous: An instance of the Lissajous class
    canvas: An instance of the MyGLCanvas class
    control: The control panel
    box: The layout sizer for the panel
    """

    def __init__(self, title, lis):
        """Initialise the GUI."""
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


if __name__ == "__main__":
    lis = Lissajous(1, 1, 0)
    app = wx.App()
    gui = Gui("Lissajous", lis)
    gui.Show(True)
    app.MainLoop()
