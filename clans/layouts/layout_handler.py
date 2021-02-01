import clans.config as cfg
import clans.data.sequences as seq
import clans.layouts.fruchterman_reingold as fr
import clans.graphics.scatter_plot_3d_vispy_temp as sp


def calculate_layout(layout):
    stop = False
    if layout == "FR":
        fr.init_variables()
        if cfg.run_params['is_graphics']:
            sp_object = sp.ScatterPlot3D()
            sp_object.start_timer()
        # If pre-defined number of rounds, perform this number of iterations
        elif cfg.run_params['num_of_rounds'] > 0:
            for i in range(cfg.run_params['num_of_rounds']):
                fr.calculate_new_positions()
            cfg.run_params['rounds_done'] = i+1
        # If the cooling parameter < 1, keep iterating as long as the temperature > 1e-5
        elif cfg.run_params['cooling'] < 1.0:
            i = 0
            while fr.current_temp > 1e-5:
                fr.calculate_new_positions()
                i += 1
            cfg.run_params['rounds_done'] = i
        # In the end of the clustering cycles, update the new coordinates in the main sequences_array
        seq.update_positions(fr.coordinates.T)
