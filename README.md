# CLANS

CLANS 2.0 is a Python-based program for clustering sequences in the 2D or 3D space, based on their sequence similarities. CLANS visualizes the dynamic clustering process and enables the user to interactively control it and explore the cluster map in various ways.

## Overview

CLANS implements a version of the Fruchterman-Reingold force directed graph layout, which uses the similarity scores to iteratively calculate attractive and repulsive forces between all pairs of sequences and move them in space accordingly. The better the score, the higher the attractive force.
The program was originally designed to cluster protein sequences based on their all-against-all sequence similarities, obtained by BLASTP (HSP E-values). However, CLANS can be generalized and applied to cluster and visualize any weighted network.
The cluster map can be saved as an image or as a file, which can later be loaded again by the CLANS software or by other network-visualizing software.

CLANS can be used in two modes:

• **GUI-based visualization tool** (default mode), which gets a matrix of sequence similarities and
displays them as a dynamic graph using the Fruchterman-Reingold force-directed layout.
In addition to clustering the sequences in space, the visualization tool enables to explore the data in various ways, which include manual interaction with the graph (rotation, panning, zoom-in and out, selection of data-points), different views of the data, several selection options, grouping and coloring the data (or a subset of it) by different features.

• **Command-line tool** (executed using the ‘-nogui’ flag), which can be used to obtain a matrix of sequence similarities by running all-against-all BLAST search. In addition, it can run the Fruchterman-Reingold force-directed graph layout for a defined number of iterations and save the results in a clans-formatted file which can later be loaded and presented in the visualization tool. This is recommended for large datasets (>5000 sequences, depending on the computer resources), in which the clustering process is slow and there is no advantage in visualizing it.
The BLAST search is only available in the command-line mode.

## Installation

**Requirements:** Anaconda installed on the target computer. An OS-specific version of Anaconda can be downloaded from: https://www.anaconda.com/.

### From source using conda:

1. Download CLANS latest release from: https://github.com/inbalpaz/CLANS/releases.

2. Extract the tar.gz file into the desired working-directory.

3. Create a new conda environment using the ‘clans_2_0.yml’ file (located in the root directory of CLANS) using the following command:

    `Conda env create -f clans_2_0.yml`
    
**Windows users:** Use the environment file ‘clans_2_0_windows.yml’ and work from within Anaconda shell command prompt.

## Usage

### Running CLANS in command-line mode

The command-line mode is executed using the ‘-nogui’ flag option. It can be used to perform a BLAST search in order to create a matrix of sequence similarities and/or to perform a specific number of iterations of the force-directed graph layout calculation (which can be later loaded and displayed in the visualizing tool). It is also recommended in cases of large datasets, where the clustering can be done in the background and the resulted clans map can later be loaded and explored using the graphical interface.

Within the activated clans_2_0 conda environment, type:

`python -m clans -nogui -infile <fasta_file_path> -saveto <destination_file_path> [options]
`

or

`python -m clans -nogui -load <network_file_path> -dorounds <number of iterations> -saveto <destination_file_path> [options]`

### Open the GUI-based visualisation tool

Within the activated clans_2_0 conda environment, type:

`python -m clans [-load <network file path>] [options]
`

When clans is executed without an input-file, the GUI is opened empty and an input-file can be loaded from the ‘File’ menu.

## Tutorial

A detailed tutorial is found here: https://github.com/inbalpaz/CLANS/tree/master/manual/Manual.pdf


or can be opened from CLANS visualisation tool (Help -> CLANS manual).
