# GO-EAST

GO-EAST is a Python/Pyomo direct-current optimal power flow (DCOPF) model for simulating synthetic weather years on a reduced representation of the U.S. Eastern Interconnection. The repository combines a 500-bus network, generator and fuel-price assumptions, hourly balancing-authority load, wind, and solar profiles, hydropower availability, and generator-outage data. It prepares one experiment directory per synthetic year and solves each annual simulation as four windows.

The model is intended for research on bulk-power-system operations under many plausible annual conditions. Its outputs include generator dispatch, line flows, bus voltage angles, load slack, nodal-balance dual values, and daily objective values.


## Repository workflow

The standard workflow has three stages:

1. `reduced_network_data_allocation.py` maps the source data to the reduced network, writes shared files under `Data/data_allocation/`, and creates one experiment directory for each selected synthetic year.
2. `EICDataSetup.py` reads the shared files and writes an `EIC_data.dat` Pyomo input file into every experiment directory.
3. `wrapper_simple.py`, copied into each experiment directory during preprocessing, solves a selected portion of the year with the model defined in `EIC_simple.py`.

With the repository defaults, an experiment directory is named:

```text
Exp500_simple_300_<year>
```

Here, `500` is the reduced-network bus count, `simple` is the model treatment, `300` is the transmission parameter used by the preprocessing script, and `<year>` is the zero-based synthetic-year index.

## Requirements

- Python 3
- A working Gurobi installation and license
- Python packages:
  - `numpy`
  - `pandas`
  - `openpyxl`
  - `xlrd`
  - `pyomo`

Install the Python dependencies in a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

Then install the packages:

```bash
python -m pip install --upgrade pip
python -m pip install numpy pandas openpyxl xlrd pyomo gurobipy
```

Confirm that Pyomo can access Gurobi before starting a long run:

```bash
python -c "from pyomo.environ import SolverFactory; print(SolverFactory('gurobi').available())"
```

The command should print `True`.

## Run the model

Run all preparation commands from the repository root. The scripts use relative paths and therefore depend on the current working directory.

### 1. Select the simulation years

Open `reduced_network_data_allocation_constfp_outage_multiyears.py` and review these settings near the beginning of the file:

```python
NODE_NUMBER = [500]
UC_TREATMENTS = ['_simple']
trans_p = [300]
years = range(0, 500)
```

The default runs synthetic years `0` through `499`. For an initial smoke test, use one year:

```python
years = range(0, 1)
```

Each selected year must have all three annual profile files:

```text
Data/Load/synthetic/BA_load_corrected_<year>.csv
Data/Gen/synthetic/BA_wind_<year>.csv
Data/Gen/synthetic/BA_solar_corrected_<year>.csv
```

### 2. Allocate data and create experiment directories

From the repository root, run:

```bash
python reduced_network_data_allocation.py
```

This step creates `Data/data_allocation/` and an experiment directory for each selected year, such as `Exp500_simple_300_0/`. It also copies the model and wrapper files needed by the experiment.

This can be a data- and compute-intensive step when all 500 years are selected. Ensure that adequate disk space is available before running the full ensemble.

### 3. Build the Pyomo input files

Still from the repository root, run:

```bash
python EICDataSetup.py
```

The script finds every matching `Exp*` directory and creates an `EIC_data.dat` file inside it. A successful build prints `Complete:` followed by the path to each generated file.

### 4. Solve one synthetic year

Change into the desired experiment directory:

```bash
cd Exp500_simple_300_0
```

The 365-day year is divided into four windows:

| Window | Days | Length |
|---:|---:|---:|
| `0` | 1–100 | 100 days |
| `1` | 101–200 | 100 days |
| `2` | 201–300 | 100 days |
| `3` | 301–365 | 65 days |

Run a window with:

```bash
python wrapper_simple.py --win 0
```

Repeat with `--win 1`, `--win 2`, and `--win 3` to cover the full year. The current wrapper uses Gurobi, a four-hour solver time limit per simulated day, and two solver threads. These settings are defined by `Solvername`, `Timelimit`, and `Threadlimit` in `wrapper_simple.py`.

The four windows write different filenames, so they may be launched as separate processes if the machine, solver license, and available memory support the combined workload. Each process must use the corresponding experiment directory as its working directory.

## Outputs

For each window `<n>`, the wrapper writes the following CSV files inside the experiment directory:

| File | Contents |
|---|---|
| `mwh_win<n>.csv` | Hourly generation by generator and fuel type |
| `flow_win<n>.csv` | Hourly transmission-line flows |
| `vlt_angle_win<n>.csv` | Hourly bus voltage angles |
| `slack_win<n>.csv` | Hourly bus-level slack |
| `duals_win<n>.csv` | Dual values for nodal-balance constraints |
| `objective_values_win<n>.csv` | Daily objective values |

Time indices in the output files refer to hours within the full synthetic year, even when a single window is solved.

## Running multiple years

After preprocessing and data setup, repeat the four-window solve inside each experiment directory. For large ensembles, use a scheduler or workflow manager and assign one experiment/window pair to each job. Avoid oversubscribing CPUs: every wrapper process requests two Gurobi threads by default.

Before automating the full ensemble, verify that:

- the single-year preprocessing step completes;
- `EIC_data.dat` exists in the experiment directory;
- Gurobi is detected and licensed;
- one short window starts solving successfully; and
- the expected CSV outputs appear in the experiment directory.

## Troubleshooting

### `No matching Exp folders found`

Run `EICDataSetup.py` from the repository root after the allocation script has created directories matching `Exp500_simple_300_<year>`.

### `Could not infer NN from folder name`

Run `wrapper_simple.py` from inside a correctly named experiment directory. Do not rename the directory unless the parsing logic is updated as well.

### Gurobi is unavailable or reports a license error

Confirm the Gurobi installation and license outside the model, then rerun the Pyomo availability check shown under Requirements.

### A required CSV or Excel file is missing

Confirm that the repository data were downloaded completely, including any large files managed outside ordinary Git. Also verify that the selected synthetic-year indices exist in all three load, wind, and solar directories.

### A solve is infeasible

Review the Gurobi/Pyomo termination message and the selected year's input data. The wrapper only loads and exports a solution when the solver reports an optimal or feasible termination condition.

