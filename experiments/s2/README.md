# WISP-DC S2 Python Reproducibility Package

## What this package validates

S2 evaluates a predefined **Llama 2 70B online-inference workload** using
official **MLPerf Inference v5.0 Server** measurements. The program recommends
an evaluated infrastructure configuration that satisfies the user's throughput,
accelerator-count, p99 TTFT, p99 TPOT, and ROUGE accuracy constraints.

This is a **benchmark-trace-based infrastructure-feasibility simulation**. It
does not execute Llama 2 70B locally and does not create new GPU measurements.

## Files

- `s2_simulation.py` — runnable model and command-line interface.
- `s2_benchmark_data.csv` — official measured benchmark inputs and URLs.
- `s2_test_cases.csv` — declared T1–T6 scenario requirements.
- `test_s2_simulation.py` — automated validation suite.
- `generated_outputs/s2_scenario_results.csv` — T1–T6 results.
- `generated_outputs/s2_detailed_results.json` — every configuration check.
- `generated_outputs/s2_sensitivity_results.csv` — throughput/resource sweep.
- `generated_outputs/s2_validation_report.txt` — human-readable test output.
- `generated_outputs/s2_run_manifest.json` — reproducibility/evidence summary.
- `generated_outputs/s2_throughput.png` — official throughput comparison.
- `generated_outputs/s2_sensitivity_map.png` — recommendation sensitivity map.

## How to run

From this folder:

```bash
python s2_simulation.py --run-all
python -m unittest -v test_s2_simulation.py
```

Example user input:

```bash
python s2_simulation.py --throughput 20000 --max-accelerators 8
```

Expected recommendation: `HPE-H100-8`.

An infeasible example:

```bash
python s2_simulation.py --throughput 20000 --max-accelerators 2
```

Expected recommendation: `None` and status `Infeasible`.

## Decision rule

1. Reject non-VALID benchmark results.
2. Apply throughput, accelerator-count, TTFT, TPOT, and ROUGE constraints.
3. Minimize accelerator count among feasible evaluated configurations.
4. If accelerator counts tie, minimize excess throughput to avoid unnecessary
   over-provisioning.
5. Return `Infeasible` when no evaluated option passes every hard constraint.

## Evidence boundary

The selected benchmark submissions do not provide matched operational server
power measurements or comparable dated full-system purchase prices. Therefore,
the program does not claim operational energy, CAPEX, TCO, ROI, or the cheapest
purchase-price system. It recommends a minimum-resource technically feasible
configuration among the four evaluated systems.

## Primary official sources

- https://github.com/mlcommons/inference_results_v5.0
- https://docs.mlcommons.org/inference_results_v5.0/
- https://doi.org/10.1109/ISCA45697.2020.00045
- https://mlcommons.org/2024/03/mlperf-llama2-70b/
- https://github.com/mlcommons/inference/blob/master/language/llama2-70b/README.md
