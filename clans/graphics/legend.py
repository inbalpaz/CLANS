import numpy as np
from vispy import app, scene


class Legend:

    def __init__(self, view):
        self.app = app.use_app('pyqt5')

        self.view = view

        self.view.camera = 'panzoom'
        self.view.camera.set_range(x=(0, 10), y=(0, 40), z=None, margin=1)

        # Create a color-bar visual for color-by param
        self.colorbar = scene.visuals.ColorBar(cmap='cool', orientation='right', size=(60, 4))
        self.colorbar.pos = (0, 20)
        self.colorbar.label = 'Sequences length'
        # self.colorbar.set_gl_state('translucent', blend=True)

    def show_colorbar(self, colormap, param_array):
        self.colorbar.parent = None

        min_param = np.amin(param_array)
        max_param = np.amax(param_array)

        # Generate and display a color-bar legend
        self.colorbar.cmap = colormap
        self.colorbar.clim = (min_param, max_param)
        self.colorbar.parent = self.view.scene

    def hide_colorbar(self):
        self.colorbar.parent = None
