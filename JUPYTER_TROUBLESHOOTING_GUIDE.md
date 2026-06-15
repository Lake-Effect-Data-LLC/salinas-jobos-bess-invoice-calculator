# Jupyter Troubleshooting Guide

Use this guide when a value in `main.ipynb` looks unexpected. The goal is to
separate three cases quickly:

- the value is a direct input from a CSV
- the value is calculated by the Python code
- the notebook is showing stale output from an older run
- the notebook is using the wrong Python environment or kernel

## First Checks

1. Confirm the notebook is using the project Python environment.
2. Restart the notebook kernel.
3. Run all cells from the top.
4. Confirm the selected project, usually `salinas` or `jobos`.
5. Re-open the output table only after the calculation cell has completed.

If a value still looks wrong after a clean run, trace it from the output column
back to its source.

## Python and Kernel Problems

The first code cell in `main.ipynb` prints the Python executable path:

```python
import sys
print(sys.executable)
```

Use that line to confirm Jupyter is running the environment you expect. If it
prints a global Python path instead of the project `.venv`, the notebook may use
different package versions from the command line.

Expected project environment on this repo:

```text
.venv
```

The dependency versions are listed in:

```text
requirements.txt
```

Current key versions:

```text
pandas==3.0.3
notebook==7.5.7
ipykernel==7.3.0
```

### Fix: Select the Right Kernel in VS Code

1. Open `main.ipynb`.
2. Click the kernel name in the upper-right corner.
3. Select the interpreter from this repo's `.venv`.
4. Restart the kernel.
5. Run all cells.

After changing the kernel, the first cell should print a path containing:

```text
salinas-jobos-bess-invoice-calculator\.venv
```

### Fix: Install the Project Kernel

From the repo root, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --user --name salinas-jobos-bess --display-name "Salinas Jobos BESS"
```

Then select `Salinas Jobos BESS` as the notebook kernel.

### Symptoms of the Wrong Python Version or Kernel

- `ModuleNotFoundError` for packages that are already installed elsewhere
- `pandas` behavior differs between notebook and terminal runs
- notebook output does not match `python .\main.py salinas`
- the first cell prints a Python path outside this repo
- VS Code keeps asking to install notebook or kernel packages

## Where Values Come From

| Output Column | Source |
| --- | --- |
| `CPP` | calculated from `cppf + cpppif` in `bess_contract_values_template.csv` |
| `MCC` | calculated in `compensation_calculator.py`, using yearly values and approved performance tests |
| `FA` | calculated from monthly availability inputs |
| `FAA` | calculated from `FA` |
| `PRA` | calculated from monthly risk-hour inputs and annual waiting-period caps |
| `MFP` | calculated as `CPP x MCC x FAA x PRA` |
| `Other_ADJ` | direct input from `bess_monthly_inputs_template.csv` |
| `ALD` | calculated availability liquidated damages |
| `CLD` | calculated capability liquidated damages from `Performance_Tests.csv` |
| `Actual_Efficiency` | calculated only when matching monthly performance data exists |
| `ELD` | calculated efficiency liquidated damages |
| `ADJ_Total` | `Other_ADJ + ALD + CLD + ELD` |
| `MP` | `MFP - ADJ_Total` |

## Common Issues

### `Other_ADJ` Has Unexpected Non-Zero Values

`Other_ADJ` is not calculated. It is read directly from the monthly input file:

```text
data/<project_id>/bess_monthly_inputs_template.csv
```

Check the `Other_ADJ` column for the same billing month. If the value appears
there, the notebook is behaving correctly.

This field is meant for manual invoice adjustments other than calculator-made
liquidated damages. Because `ALD`, `CLD`, and `ELD` are already included in
`ADJ_Total`, any non-zero `Other_ADJ` should be reviewed to avoid double
counting.

### `Actual_Efficiency` Shows `NaN`

This usually means there is no matching row in:

```text
data/<project_id>/Monthly_Performance_Guarantee.csv
```

The match is based on both `timestamp_month` and `agreement_year`. If a monthly
performance row is missing, `Actual_Efficiency` stays blank and `ELD` remains
zero.

### A Warning Mentions `Other_ADJ`

The warning is intentional. It means a monthly input row has a non-zero
`Other_ADJ` and should be reviewed before invoice use.

It does not mean the calculation failed.

### Values Change After Running Cells

Notebook output can be stale if only some cells were rerun. Restart the kernel
and run all cells before investigating the formulas.

If the table still differs from the CSV output, compare against:

```text
output/<project_id>/bess_monthly_results.csv
```

## Fast Trace Workflow

1. Identify the billing month and output column.
2. Check whether the column is direct input or calculated using the table above.
3. For direct inputs, inspect the matching project CSV row.
4. For calculated values, inspect the related formula in:

```text
compensation_calculator.py
calculations.py
```

5. Re-run:

```powershell
python .\main.py salinas
python .\main.py jobos
```

6. Compare the notebook table with `output/<project_id>/bess_monthly_results.csv`.
