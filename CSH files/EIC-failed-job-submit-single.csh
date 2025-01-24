#!/bin/tcsh

# Set up conda and gurobi environment

module load gurobi
conda activate /usr/local/usrapps/infews/GO_env

# Submit multiple jobs at once

set folNameBase = Exp

foreach Year (`seq 1980 2019`)

	#foreach NN ( 500 525 550 575 600 625 650 675 700 )
	foreach NN ( 500 )
	#foreach NN ( 525 550 575 600 625 650 675 700 )

		foreach SC ( _1 _2 _3 _4 )

			foreach UC ( _simple_ )

				#foreach TC ( 25 50 75 100 200 300 400 500 )
				foreach TC ( 300 )

					set dirName = ${folNameBase}${NN}${UC}${TC}_${Year}${SC}
	   				#d /share/infews/kakdemi/IM3_Final_Runs/IM3_WECC/UCED/Simulation_folders/$dirName/Outputs
	   				cd $dirName

					if (-f duals.csv) then
						cd ..

					else
						#cd ..
						echo "Simulation failed for $dirName."
				
						if ($UC == _simple_) then

							# Submit LSF job for the directory $dirName
	   						bsub -n 2 -R "span[hosts=1]" -R "rusage[mem=14GB]" -W 5760 -o out.%J -e err.%J "python wrapper_simple${SC}.py"
							# Go back to upper level directory
	    					cd ..

						else if ($UC == _coal_) then

							# Submit LSF job for the directory $dirName
	   						bsub -n 2 -R "span[hosts=1]" -R "rusage[mem=14GB]" -W 5760 -o out.%J -e err.%J "python wrapper_coal.py"
							# Go back to upper level directory
	    					cd ..

	    				endif
					endif

				end
			end
		end
	end
end

conda deactivate