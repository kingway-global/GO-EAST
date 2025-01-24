#!/bin/tcsh

# Copy output files at once

conda activate /usr/local/usrapps/infews/GO_env
mkdir -p /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs

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
					cd /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/$dirName

					if (-f duals.csv) then

						cp duals.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/duals_${NN}${UC}${TC}_${Year}${SC}.csv
						cp flow.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/flow_${NN}${UC}${TC}_${Year}${SC}.csv
						cp mwh.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/mwh_${NN}${UC}${TC}_${Year}${SC}.csv
						cp slack.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/slack_${NN}${UC}${TC}_${Year}${SC}.csv
						cp vlt_angle.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/vlt_angle_${NN}${UC}${TC}_${Year}${SC}.csv
						cp objective_values.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/objective_values_${NN}${UC}${TC}_${Year}${SC}.csv
						cp nodal_load.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/nodal_load_${NN}.csv
						cp must_run.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/must_run_${NN}.csv
						cp thermal_gens.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/thermal_gens_${NN}.csv
						#cp gen_mat_full.csv /share/infews/jqian4/GO_EAST_fp_outage_multiyears_500/outputs/gen_mat_full_${NN}${UC}${TC}_${Year}${SC}.csv

						#cd /share/infews/kakdemi/IM3_runs_2019/$dirName/Inputs

						#cp data_genparams.csv /share/infews/kakdemi/IM3_runs_all/WECC_2019/data_genparams_${NN}${UC}${TC}${HD}${YE}.csv
						#cp must_run.csv /share/infews/kakdemi/IM3_runs_all/WECC_2019/must_run_${NN}${UC}${TC}${HD}${YE}.csv
						#cp line_params.csv /share/infews/kakdemi/IM3_runs_all/WECC_2019/line_params_${NN}${UC}${TC}${HD}${YE}.csv
						#cp nodal_load.csv /share/infews/kakdemi/IM3_runs_all/WECC_2019/nodal_load_${NN}${UC}${TC}${HD}${YE}.csv

					else
						echo "Simulation failed for $dirName."

					endif

				end
			end
		end
	end
end

conda deactivate
