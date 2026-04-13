# Export Adapter

## Setup

Create/activate a virtualenv (optional) and install deps:

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## Required input files

In the `inputs` directory, add these CSV files (as defined in `main.py`):
 - `inputs/direct-emissions.csv`
 - `inputs/energies.csv`
 - `inputs/eol.csv`
 - `inputs/materials.csv`
 - `inputs/other-requirements.csv`
 - `inputs/processing-methods.csv`
 - (and/or any other additional files listed under `FILES` in `main.py`)

The CSV expected in inputs have a specific format, the easiest way to match it is to complete your data based on the GDrive template we can give you (at least for the moment.. any contribution is welcome!).

## Run the script
```bash
python main.py
```

## Where to find outputs

Generated `.csv` and `.js` are written to `outputs/`, per each entry’s configured targets (e.g., midpoints, endpoints, contributions).

Example (from materials):
 - outputs/js/materials_midpoints.js
 - outputs/js/materials_endpoints.js
 - outputs/js/materials_contributions.js
