#!/bin/tcsh

# Set up conda environment

conda activate /usr/local/usrapps/infews/group_env

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
		   			cd $dirName

					# Submit LSF job for the directory $dirName
		   			bsub -n 1 -R "span[hosts=1]" -R "rusage[mem=5GB]" -W 5000 -o out.%J -e err.%J "python EICDataSetup.py"
					# Go back to upper level directory
		    		cd ..

				end
			end
		end
	end
end

conda deactivate
