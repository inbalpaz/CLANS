import time
import clans.config as cfg
import clans.clans.data.sequences as seq
import clans.clans.layouts.fruchterman_reingold as fr


def calculate_layout(layout):
    if layout == "FR":
        fr.init_variables()
        # If pre-defined number of rounds, perform this number of iterations
        if cfg.run_params['num_of_rounds'] > 0:
            before = time.time()

            # If the cooling parameter < 1, keep iterating as long as the temperature > 1e-5
            if cfg.run_params['cooling'] < 1.0:
                i = 0
                while fr.current_temp > 1e-5:
                    fr.calculate_new_positions()
                    i += 1

                    if i % 100 == 0:
                        after = time.time()
                        duration = after - before
                        print("The calculation of " + str(i+1) + " rounds took " + str(duration) + " seconds")

                cfg.run_params['rounds_done'] = i

            # Iterate for the requested number of rounds
            else:
                for i in range(cfg.run_params['num_of_rounds']):
                    fr.calculate_new_positions()

                    if (i+1) % 100 == 0:
                        after = time.time()
                        duration = after - before
                        print("The calculation of " + str(i+1) + " rounds took " + str(duration) + " seconds")

                cfg.run_params['rounds_done'] = i+1

        # If the cooling parameter < 1, keep iterating as long as the temperature > 1e-5
        elif cfg.run_params['cooling'] < 1.0:
            i = 0
            while fr.current_temp > 1e-5:
                fr.calculate_new_positions()
                i += 1
            cfg.run_params['rounds_done'] = i

        # In the end of the clustering cycles, update the new coordinates in the main sequences_array
        seq.update_positions(fr.coordinates.T, 'full')
