# Paper artifact scope

## Active S1 profile versus historical S1

The Drive-supplied `simulate_s1.py` is preserved without edits in `archive/s1_original/`, with its expected input/output directory structure. Its earlier nine-check validation includes three cloud-budget cases using a regional EUR 9.30 GPU-hour assumption. The manuscript explicitly excludes those price-dependent cases.

The active copy in `experiments/s1/` retains the training, deadline selection, proxy-energy, heat, physical/rack, PUE and manual arithmetic logic. Its input path is made local to the experiment, its output directory is created automatically, tariff/price constants and numeric financial calculations are removed, and CT-07–CT-09 are omitted. The `cloud_cost_eur_run` field remains null; `budget_feasibility` is empty and `price_optimization_performed` is false. No zero price is substituted for missing evidence. `reproduce.py` rejects price-bearing output in this profile.

No benchmark input values or manuscript English were edited while assembling this repository. The current manuscript is a copy of the supplied, previously checked single-column version. The bibliography and citation numbering retain the corrected original-ZIP values.

## Active S2

The S2 implementation, input CSVs, six case profiles and eighteen unit tests are copied from the supplied complete package without rewriting them. The run regenerates scenario, detailed, sensitivity and manifest files. Static original figure assets remain in `paper/figures/`; optional plotting scripts regenerate performance visualizations separately.

## Prototype support

Hardware tables, rule-book CSVs and formula workbooks are provided as supporting prototype design material. Their inclusion does not validate every rule, product field, facility constraint, cooling formula, CPU/networking/storage option or future workflow. Current and earlier rule variants are retained in separate directories, including `workload_prev`. Some files have identical content and are retained where their supplied folder histories differ.

## What the recorded validation establishes

The executed result is six retained S1 checks plus eighteen S2 unit tests, eight S1 deadline decisions, six expected S2 decisions, and 99 S2 sensitivity combinations. The tests operate on supplied official-result extracts and their source URLs. They do not establish independent physical measurement, complete hardware-catalogue coverage, current prices, real operating-plant PUE or monetary optimality.
