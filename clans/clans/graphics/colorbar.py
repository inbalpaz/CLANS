import numpy as np
from vispy import app, scene


class Colorbar:

    def __init__(self, view):
        self.app = app.use_app('pyqt5')

        self.view = view

        self.view.camera = 'panzoom'
        self.view.camera.set_range(x=(0, 10), y=(0, 40), z=None, margin=1)

        # Create a color-bar visual for color-by param
        self.colorbar = scene.visuals.ColorBar(cmap='cool', orientation='right', size=(60, 2))
        self.colorbar.pos = (0, 20)
        self.colorbar.label = 'Sequences length'

    def show_colorbar(self, colormap, param_name, min_val, max_val):
        self.colorbar.parent = None

        # Generate and display a color-bar legend
        self.colorbar.cmap = colormap

        # Because of a bug in the colorbar visual (it is displayed upside down) - switch the order of the min/max values
        #self.colorbar.clim = (min_val, max_val)
        self.colorbar.clim = (max_val, min_val)

        self.colorbar.label = param_name

        self.colorbar.parent = self.view.scene

    def hide_colorbar(self):
        self.colorbar.parent = None
