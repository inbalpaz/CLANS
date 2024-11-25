# CLANS

CLANS_2 is a Python-based program for clustering sequences in the 2D or 3D space, based on their sequence
similarities. CLANS visualizes the dynamic clustering process and enables the user to interactively control it and
explore the cluster map in various ways.

## Overview

CLANS implements a version of the Fruchterman-Reingold force directed graph layout, which uses the similarity scores to iteratively calculate attractive and repulsive forces between all pairs of sequences and move them in space accordingly. The better the score, the higher the attractive force.
The program was originally designed to cluster protein sequences based on their all-against-all sequence similarities, obtained by BLASTP (HSP E-values). However, CLANS can be generalized and applied to cluster and visualize any weighted network.
The cluster map can be saved as an image or as a file, which can later be loaded again by the CLANS software or by other network-visualizing software.

CLANS can be used in two modes:

• **GUI-based visualization tool**: gets a matrix of sequence similarities and
displays them as a dynamic graph using the Fruchterman-Reingold force-directed layout.
In addition to clustering the sequences in space, the visualization tool enables to explore the data in various ways,
which include manual interaction with the graph (rotation, panning, zoom-in and out, selection of data-points),
different views of the data, several selection options, grouping and coloring the data (or a subset of it) by different
features.

• **Command-line tool**: can be used to obtain a matrix of sequence similarities by running all-against-all BLAST
search.
In addition, it can run the Fruchterman-Reingold force-directed graph layout for a defined number of iterations
and save the results in a clans-formatted file which can later be loaded and presented in the visualization tool.
This is recommended for large datasets (>5000 sequences, depending on the computer resources),
in which the clustering process is slow and there is no advantage in visualizing it.

The BLAST search is only available in the command-line mode and requires Blast+ installation on the target computer.

## Installation

**Requirements:** Anaconda or Miniconda installed on the target computer. An OS-specific version can be downloaded
from: https://www.anaconda.com/.

### From source using conda:

1. Download CLANS latest release from: https://github.com/inbalpaz/CLANS/releases.

2. Extract the tar.gz file into the desired working-directory.

3. Create a new conda environment using the ‘clans_2_1.yml’ file (located in the root directory of CLANS) using the
   following command:

   `conda env create -f clans_2_2.yml`

4. Activate the newly created environment: `conda activate clans_2_2`

**Please note:** the GUI-based visualization tool may not work properly on linux.
It is recommended to use it in MacOS / Windows.
The command-line tool can be run on linux without a problem.

## Usage

### The GUI-based visualization tool

#### Open the visualisation tool:

Within the activated clans_2_2 conda environment, type:

`python -m clans [-load <network file path>] [options]
`

When clans is executed without an input-file, the GUI is opened empty and an input-file can be loaded from the ‘File’
menu.

#### Input files:

1. **Mandatory input**: CLANS visualisation tool gets a network file, containing pairs of sequence identifiers and their
   pairwise similarity scores.
   It accepts two file formats:
    - clans format (.clans), which can be obtained by running CLANS command-line tool with blast search.
    - Tab-delimited file (.tsv).

2. **Optional input**: Metadata files in tab-delimited format.

#### Output files:

1. **Network file**: The current session of CLANS can be saved in one the accepted file formats.
    - clans format, which saves the exact state of the session, including the coordinates
      and all other customized parameters and can be used to restore the session in the GUI.
    - Tab-delimited file, which can be read by other network visualization software.

2. **Save as image**: The graph area of the current CLANS session can be saved as an image in one of the following
   formats: PNG, Tiff, Jpeg and EPS.

All the visualization-related options (clustering, grouping, coloring, etc.)
are described in detail in CLANS manual: https://github.com/inbalpaz/CLANS/tree/master/clans/manual/Manual.pdf

### Running CLANS in command-line mode

The command-line mode is executed using the ‘-nogui’ flag option. It can be used to perform a BLAST search in order to
create a matrix of sequence similarities and/or to perform a specific number of iterations of the force-directed graph
layout calculation (which can be later loaded and displayed in the visualizing tool). It is also recommended in cases of
large datasets, where the clustering can be done in the background and the resulted clans map can later be loaded and
explored using the graphical interface.

**Start from fasta sequences and run BLAST search to get all vs. all sequence similarities**:

- Run BLAST only and save the output in clans format:

  `python -m clans -nogui -infile <fasta_file_path> -saveto <destination_file_path> [blast-related options]
  `

- Run BLAST and perform N iterations of clustering. Save the output in clans format:

  `python -m clans -nogui -infile <fasta_file_path> -saveto <destination_file_path> -dorounds <N> [options]`

**Input is a network file (in clans format or tsv): perform N iterations of clustering**

`python -m clans -nogui -load <network_file_path> -dorounds <N> -saveto <destination_file_path> [options]`

### A description of all CLANS command line arguments:

```
usage: python -m clans [-h] [-nogui] [-load network_file_path] [-input_format input_file_format] 
                       [-infile fasta_file_path] [-cores number_of_cores] [-eval E-value_threshold] 
                       [-matrix scoring_matrix] [-dorounds rounds] [-pval similarity_threshold] 
                       [-saveto destination_file_path] [-output_format output_file_format] [-cluster2d]
                       [--cooling COOLING] [--maxmove MAXMOVE] [--att_val ATT_VAL] [--att_exp ATT_EXP] 
                       [--rep_val REP_VAL] [--rep_exp REP_EXP] [--dampening DAMPENING] [--gravity GRAVITY] 
                       [--debug]

General options:
  -h, --help            show this help message and exit

  -nogui                Run CLANS in command-line mode (for performing BLAST search or clustering large datasets)
  --debug               Debug mode: add debug printouts

Input/Output options:
  -load network_file_path
                        Load a network file containing at least pairs of sequences and similarity-scores
  -input_format input_file_format
                        Input file format (clans/delimited. default is 'clans' format)
  -infile fasta_file_path
                        a FASTA file input for BLAST search
  -saveto destination_file_path
                        A destination path for saving the output file (in CLANS format, by default)
  -output_format output_file_format
                        Output file format (clans/delimited. default is 'clans' format)
                        
BLAST related options:
  -cores number_of_cores
                        The number of cores to use for BLAST multi-processing execution. (Optional, default is the number of computer available
                        cores).
  -eval E-value_threshold
                        E-value threshold for extracting BLAST HSPs (default=0.01)
  -matrix scoring_matrix
                        Scoring matrix for BLAST search (default:BLOSUM62)
                        
Clustering options:
  -dorounds rounds      Number of clustering rounds to perform (default=0)
  -pval similarity_threshold
                        Similarity threshold (default=0.0001)
  -cluster2d            Perform the clustering in 2D instead of 3D (default: cluster in 3D)
  --cooling COOLING     A multiplier for 'maxmove'. By default, set to 1 which causes the graph to keep moving until the user stops
                        it. When cooling<1, maxmove gradually converges to 0 and the graph points stop moving.
  --maxmove MAXMOVE     The maximum distance a point is allowed to move per iteration (default=0.1)
  --att_val ATT_VAL     A multiplier factor for the calculation of the attractive force between each two sequences (default=10.0)
  --att_exp ATT_EXP     Determines how the attractive force scales with the distance between each two vertices in the graph
                        (default=1), attraction increases linearly with the distance
  --rep_val REP_VAL     A multiplier factor for the calculation of the repulsive force between each two sequences (default=10.0)
  --rep_exp REP_EXP     Determines how the repulsive force scales with the distance between each two vertices in the graph
                        (default=1), repulsion decreases linearly with the distance
  --dampening DAMPENING
                        A value between 0 and 1, determines to what extent the movement vector of the last movement affects the
                        current movement. The lower it is, the greater the last movement's influence (default=0.2)
  --gravity GRAVITY     A minimal force that attracts each sequence towards the origin of the graph and prevents unconnected
                        clusters/sequences from drifting apart indefinitely. It scales linearly with the distance from origin
                        (default=1.0)
```

## Tutorial

A detailed tutorial is found here: https://github.com/inbalpaz/CLANS/tree/master/clans/manual/Manual.pdf

or can be opened from CLANS visualisation tool (Help -> CLANS manual).
