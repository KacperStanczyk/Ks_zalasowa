# Behavior Matrix Toolkit

This repository now contains a self-contained prototype implementation of the
Behavior Matrix specification.  The toolkit can validate matrix files,
produce deterministic candidates for test cases (TC), and generate the
required visualisations.

## Installation

Install the dependencies from `requirements.txt` in your virtual environment.
The toolkit relies on `PyYAML`, `jsonschema`, `pandas`, `matplotlib`,
`networkx`, and `plotly`.

```bash
pip install -r requirements.txt
```

## Example data

A minimal set of sample files is available in `examples/behavior_matrix/`:

* `matrix.yaml` – editable YAML source with three matrix rows.
* `matrix.csv` – CSV representation of the same data set.
* `policy.json` – example generation policy.

## CLI usage

The CLI entry point is provided by `behavior_matrix.cli`.  Run it with
`python -m behavior_matrix.cli` or install the project and use the `bm`
command.

### Validate a matrix file

```bash
python -m behavior_matrix.cli validate --in examples/behavior_matrix/matrix.yaml
```

Exit codes:

* `0` – validation succeeded.
* `2` – schema or business-rule validation errors.
* `3` – duplicate matrix rows detected.
* `1` – unexpected internal error.

### Generate TC candidates

```bash
python -m behavior_matrix.cli gen \
  --in examples/behavior_matrix/matrix.yaml \
  --out candidates.json \
  --seed 1337 \
  --policy examples/behavior_matrix/policy.json
```

The command stops with the validation exit codes if the matrix is invalid.
On success the resulting candidates are written to `candidates.json` and a
summary message is printed.

### Visualisations

```bash
python -m behavior_matrix.cli viz \
  --in examples/behavior_matrix/matrix.yaml \
  --out out_dir
```

This creates the following artefacts:

* `transitions_<component>.png` – component-specific transition graphs.
* `heatmap.png` – coverage heatmap.
* `timing_pivot.png` – timing pivot table.
* `tc_table.html` – interactive candidate list.

All commands log human-readable information to stdout and report errors on
stderr.
