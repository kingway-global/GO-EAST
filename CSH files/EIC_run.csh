#!/bin/tcsh

# =========================================================
# EIC batch runner for the restructured East DCOPF workflow
# Supports both transmission-expansion modes:
#   +%  folders: Exp500_simple_300_2019
#   +MW folders: Exp500_simple_MW_25_2019
#
# Expected per-folder files:
#   EIC_data.dat
#   EIC_simple.py
#   wrapper_simple.py
#
# The wrapper is run four times per case:
#   python wrapper_simple.py --win 0
#   python wrapper_simple.py --win 1
#   python wrapper_simple.py --win 2
#   python wrapper_simple.py --win 3
# =========================================================

# Set up conda and gurobi environment
#conda activate /usr/local/usrapps/infews/group_env
module load gurobi
source /usr/local/apps/gurobi/gurobi810/linux64/bin/gurobi.sh

# -----------------------------
# User settings
# -----------------------------
set folNameBase = Exp

# Years to run
# For the new GADS raw-available-capacity workflow, use the years for which
# HorizonGenLimits_base_${NN}_y_${Year}.csv has been generated.
foreach Year ( 2019 )

    # Reduced-network sizes
    foreach NN ( 500 )

        # UC treatments. Use names without leading/trailing underscores here.
        foreach UC ( simple )

            # Percent transmission-expansion cases.
            # Folder example: Exp500_simple_300_2019
            foreach TC ( -20 -10 0 25 50 100 200 300 )
                set dirName = ${folNameBase}${NN}_${UC}_${TC}_${Year}

                if ( -d ${dirName} ) then
                    cd ${dirName}

                    foreach WIN ( 0 1 2 3 )
                        bsub -n 2 -R "span[hosts=1]" -R "rusage[mem=20GB]" -W 5760 \
                            -o out_win${WIN}.%J -e err_win${WIN}.%J \
                            "conda run -p /usr/local/usrapps/infews/jqian4/env_jqian4 python wrapper_${UC}.py --win ${WIN}"
                    end

                    cd ..
                else
                    echo "Warning: directory not found, skipping ${dirName}"
                endif
            end

            # Additive-MW transmission-expansion cases.
            # Folder example: Exp500_simple_MW_25_2019
            foreach TC_MW ( 25 50 75 100 300 )
                set dirName = ${folNameBase}${NN}_${UC}_MW_${TC_MW}_${Year}

                if ( -d ${dirName} ) then
                    cd ${dirName}

                    foreach WIN ( 0 1 2 3 )
                        bsub -n 2 -R "span[hosts=1]" -R "rusage[mem=20GB]" -W 5760 \
                            -o out_win${WIN}.%J -e err_win${WIN}.%J \
                            "conda run -p /usr/local/usrapps/infews/jqian4/env_jqian4 python wrapper_${UC}.py --win ${WIN}"
                    end

                    cd ..
                else
                    echo "Warning: directory not found, skipping ${dirName}"
                endif
            end

        end
    end
end

#conda deactivate
