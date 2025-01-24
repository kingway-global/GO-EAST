#!/bin/tcsh

# Set up conda environment

conda activate /usr/local/usrapps/infews/group_env

# Submit multiple jobs at once

bsub -n 2 -R "span[hosts=1]" -R "rusage[mem=14GB]" -W 5000 -o out.%J -e err.%J "python reduced_network_data_allocation_fp_outage_multiyears.py"

conda deactivate
