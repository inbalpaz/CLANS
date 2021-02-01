import argparse
import clans.config as cfg


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("-load", metavar="clans_file_path", help="Load an existing CLANS file", type=str)
    parser.add_argument("-logfile", metavar="clans_logfile_path", help="a destination file for logging", type=str)

    ## Clustering parameters
    parser.add_argument("-dorounds", metavar="rounds", help="Number of clustering rounds to perform (default=0)",
                        type=int, default=0)
    parser.add_argument("-pval", metavar="similarity_threshold", help="Similarity threshold (default="
                                                                      + str(cfg.similarity_cutoff) + ")", type=float,
                        default=cfg.similarity_cutoff)

    ## Fruchterman-Reingold arguments
    parser.add_argument("-cluster2d", help="Perform the clustering in 2D instead of 3D (default: cluster in 3D)",
                        action='store_true', default=False)
    parser.add_argument("--cooling", help="A multiplier for 'maxmove'. By default, set to 1 which causes the graph "
                                          "to keep moving until the user stops it. When cooling<1, maxmove gradually "
                                          "converges to 0 and the graph points stop moving.", type=float,
                        default=cfg.layouts['FR']['params']['cooling'])
    parser.add_argument("--maxmove", help="The maximum distance a point is allowed to move per iteration "
                                          "(default=" + str(cfg.layouts['FR']['params']['maxmove']) + ")",
                        type=float, default=cfg.layouts['FR']['params']['maxmove'])
    parser.add_argument("--att_val", help="A multiplier factor for the calculation of the attractive force between each"
                                          " two sequences (default=" + str(
        cfg.layouts['FR']['params']['att_val']) + ")",
                        type=float, default=cfg.layouts['FR']['params']['att_val'])
    parser.add_argument("--att_exp", help="Determines how the attractive force scales with the distance between each "
                                          "two vertices in the graph (default=" + str(
        cfg.layouts['FR']['params']['att_exp'])
                                          + "), attraction increases linearly with the distance",
                        type=int, default=cfg.layouts['FR']['params']['att_exp'])
    parser.add_argument("--rep_val", help="A multiplier factor for the calculation of the repulsive force between each"
                                          " two sequences (default=" + str(
        cfg.layouts['FR']['params']['rep_val']) + ")",
                        type=float, default=cfg.layouts['FR']['params']['rep_val'])
    parser.add_argument("--rep_exp", help="Determines how the repulsive force scales with the distance between each "
                                          "two vertices in the graph (default=" + str(
        cfg.layouts['FR']['params']['rep_exp'])
                                          + "), repulsion decreases linearly with the distance",
                        type=int, default=cfg.layouts['FR']['params']['rep_exp'])
    parser.add_argument("--dampening", help="A value between 0 and 1, determines to what extent the movement vector of "
                                            "the last movement affects the current movement. The lower it is, the "
                                            "greater the last movement's influence (default="
                                            + str(cfg.layouts['FR']['params']['dampening']) + ")",
                        type=float, default=cfg.layouts['FR']['params']['dampening'])
    parser.add_argument("--gravity", help="A minimal force that attracts each sequence towards the origin of the graph "
                                          "and prevents unconnected clusters/sequences from drifting apart indefinitely"
                                          ". It scales linearly with the distance from origin (default="
                                          + str(cfg.layouts['FR']['params']['gravity']) + ")",
                        type=float, default=cfg.layouts['FR']['params']['gravity'])

    args = parser.parse_args()

    if args.load is not None:
        cfg.run_params['input_file'] = args.load
        cfg.run_params['input_format'] = 'clans'
    else:
        cfg.run_params['input_file'] = None
    if args.logfile is not None:
        cfg.run_params['logfile'] = args.logfile
    else:
        cfg.run_params['logfile'] = "logfile.txt"

    cfg.run_params['num_of_rounds'] = args.dorounds
    cfg.run_params['similarity_cutoff'] = args.pval
    cfg.run_params['cooling'] = args.cooling
    cfg.run_params['maxmove'] = args.maxmove
    cfg.run_params['att_val'] = args.att_val
    cfg.run_params['att_exp'] = args.att_exp
    cfg.run_params['rep_val'] = args.rep_val
    cfg.run_params['rep_exp'] = args.rep_exp
    cfg.run_params['dampening'] = args.dampening
    cfg.run_params['gravity'] = args.gravity
    if args.cluster2d:
        cfg.run_params['dimensions_num_for_clustering'] = 2
    else:
        cfg.run_params['dimensions_num_for_clustering'] = 3

    for i in cfg.run_params:
        print(i, cfg.run_params[i])


def parse_arguments_cmd():
    parser = argparse.ArgumentParser()

    ## I/O parameters
    parser.add_argument("-infile", metavar="fasta_file_path", help="a FASTA file input for BLAST search", type=str)
    parser.add_argument("-load", metavar="clans_file_path", help="Load an existing CLANS file", type=str)
    parser.add_argument("-saveto", metavar="destination_file_path", help="a destination path for saving the output "
                                                                         "CLANS file", type=str)
    parser.add_argument("-logfile", metavar="clans_logfile_path", help="a destination file for logging", type=str)
    parser.add_argument("-graphics", help="Open the graphical interface", action='store_true', default=False)

    ## Blast search parameters
    parser.add_argument("-eval", metavar="E-value_threshold", help="E-value threshold for extracting BLAST HSPs "
                                                                   "(default="+str(cfg.BLAST_Evalue_cutoff)+")",
                        type=float, default=cfg.BLAST_Evalue_cutoff)
    parser.add_argument("-matrix", metavar="scoring_matrix", help="Scoring matrix for BLAST search (default:"
                        + cfg.BLAST_scoring_matrix + ")" , type=str,
                        choices=['BLOSUM62', 'BLOSUM45', 'BLOSUM80', 'PAM30', 'PAM70'], default=cfg.BLAST_scoring_matrix)

    ## Clustering parameters
    parser.add_argument("-dorounds", metavar="rounds", help="Number of clustering rounds to perform (default=0)",
                        type=int, default=0)
    parser.add_argument("-pval", metavar="similarity_threshold", help="Similarity threshold (default="
                        + str(cfg.similarity_cutoff) + ")", type=float, default=cfg.similarity_cutoff)

    ## Fruchterman-Reingold arguments
    parser.add_argument("-cluster2d", help="Perform the clustering in 2D instead of 3D (default: cluster in 3D)",
                        action='store_true', default=False)
    parser.add_argument("--cooling", help="A multiplier for 'maxmove'. By default, set to 1 which causes the graph "
                                          "to keep moving until the user stops it. When cooling<1, maxmove gradually "
                                          "converges to 0 and the graph points stop moving.", type=float,
                        default=cfg.layouts['FR']['params']['cooling'])
    parser.add_argument("--maxmove", help="The maximum distance a point is allowed to move per iteration "
                                          "(default="+str(cfg.layouts['FR']['params']['maxmove'])+")",
                        type=float, default=cfg.layouts['FR']['params']['maxmove'])
    parser.add_argument("--att_val", help="A multiplier factor for the calculation of the attractive force between each"
                                          " two sequences (default="+str(cfg.layouts['FR']['params']['att_val'])+")",
                        type=float, default=cfg.layouts['FR']['params']['att_val'])
    parser.add_argument("--att_exp", help="Determines how the attractive force scales with the distance between each "
                                          "two vertices in the graph (default="+str(cfg.layouts['FR']['params']['att_exp'])
                                          + "), attraction increases linearly with the distance",
                        type=int, default=cfg.layouts['FR']['params']['att_exp'])
    parser.add_argument("--rep_val", help="A multiplier factor for the calculation of the repulsive force between each"
                                          " two sequences (default="+str(cfg.layouts['FR']['params']['rep_val'])+")",
                        type=float, default=cfg.layouts['FR']['params']['rep_val'])
    parser.add_argument("--rep_exp", help="Determines how the repulsive force scales with the distance between each "
                                          "two vertices in the graph (default="+str(cfg.layouts['FR']['params']['rep_exp'])
                                          + "), repulsion decreases linearly with the distance",
                        type=int, default=cfg.layouts['FR']['params']['rep_exp'])
    parser.add_argument("--dampening", help="A value between 0 and 1, determines to what extent the movement vector of "
                                            "the last movement affects the current movement. The lower it is, the "
                                            "greater the last movement's influence (default="
                                            + str(cfg.layouts['FR']['params']['dampening']) + ")",
                        type=float, default=cfg.layouts['FR']['params']['dampening'])
    parser.add_argument("--gravity", help="A minimal force that attracts each sequence towards the origin of the graph "
                                          "and prevents unconnected clusters/sequences from drifting apart indefinitely"
                                          ". It scales linearly with the distance from origin (default="
                                          + str(cfg.layouts['FR']['params']['gravity']) + ")",
                        type=float, default=cfg.layouts['FR']['params']['gravity'])

    args = parser.parse_args()

    ## Assign the given arguments to the global 'run_params' dict
    if args.infile is not None:
        cfg.run_params['input_file'] = args.infile
        cfg.run_params['input_format'] = 'fasta'
        cfg.run_params['run_blast'] = True
    else:
        if args.load is not None:
            cfg.run_params['input_file'] = args.load
            cfg.run_params['input_format'] = 'clans'
            cfg.run_params['run_blast'] = False
        else:
            cfg.run_params['error'] = "You must provide an input file - either a FASTA file for BLAST search " \
                                      "(using -infile) or an existing CLANS file (using -load)"
            return
    if args.saveto is not None:
        cfg.run_params['output_file'] = args.saveto
    else:
        cfg.run_params['output_file'] = None
    if args.logfile is not None:
        cfg.run_params['logfile'] = args.logfile
    else:
        cfg.run_params['logfile'] = "logfile.txt"

    cfg.run_params['evalue_cutoff'] = args.eval
    cfg.run_params['scoring_matrix'] = args.matrix
    cfg.run_params['num_of_rounds'] = args.dorounds
    cfg.run_params['similarity_cutoff'] = args.pval
    cfg.run_params['cooling'] = args.cooling
    cfg.run_params['maxmove'] = args.maxmove
    cfg.run_params['att_val'] = args.att_val
    cfg.run_params['att_exp'] = args.att_exp
    cfg.run_params['rep_val'] = args.rep_val
    cfg.run_params['rep_exp'] = args.rep_exp
    cfg.run_params['dampening'] = args.dampening
    cfg.run_params['gravity'] = args.gravity
    if args.cluster2d:
        cfg.run_params['dimensions_num_for_clustering'] = 2
    else:
        cfg.run_params['dimensions_num_for_clustering'] = 3
    if args.graphics:
        cfg.run_params['is_graphics'] = True
    else:
        cfg.run_params['is_graphics'] = False

    for i in cfg.run_params:
        print(i, cfg.run_params[i])



