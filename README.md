# WISP-DC

Research artifacts for **WISP-DC: A Benchmark-Trace-Based Feasibility Framework for Workload-Specific AI Infrastructure Planning**.

Authors: Raazia Imran Reshamwala, Syed Muhammad Sheraz and Maham Faisal.

WISP-DC screens published AI-system configurations against workload requirements and ranks only feasible candidates. S1 replays MLPerf Training v4.0 ResNet-50 extracts; S2 replays MLPerf Inference v5.0 Llama 2 70B Server extracts. These programs do not train ResNet-50 or execute Llama inference locally.

## Reproduce the paper results

The core replay uses the Python standard library. It was checked with Python 3.12.14.

```bash
git clone https://github.com/Raazia-Imran/WISP-DC.git
cd WISP-DC
python reproduce.py
```

On Windows, `py reproduce.py` is also suitable. No GPU, model download or live benchmark-server request is needed.

Expected coverage:

| Check | Result |
| --- | --- |
| S1 retained technical checks | 6/6 |
| S2 unit tests | 18/18 |
| Supported automated checks in total | 24 |
| S1 deadline cases | 8 |
| S2 predefined cases matching the supplied workbook | 6/6 |
| S2 sensitivity combinations | 99 |

The latest recorded replay is in [validation/reproduction_summary.json](validation/reproduction_summary.json); the complete S2 test log is in [validation/s2_unittest.txt](validation/s2_unittest.txt). These counts validate the supplied extraction/decision pipeline, not an independent rerun of the physical MLPerf workloads.

## Repository contents

| Directory | Contents and role |
| --- | --- |
| [experiments/s1](experiments/s1) | Paper-profile training simulator, six-system/30-run extracts and regenerated technical results |
| [experiments/s2](experiments/s2) | Original inference simulator, four-system inputs, six cases, eighteen tests, plotting code and outputs |
| [workbooks](workbooks) | Final combined S1/S2 workbook, byte-identical to the workbook supplied inside the S2 package |
| [validation](validation) | Executed test logs and reproduction summary |
| [prototype](prototype) | Hardware catalogue, rule/evidence tables and eight formula workbooks; broader prototype support rather than extra validated performance evidence |
| [archive](archive) | Unmodified historical code, original packages, intermediate workbooks and research notes |
| [references](references) | Paper bibliography, references workbook, literature matrix and benchmark-source index |
| [paper](paper) | Current single-column working manuscript and original figure assets; English preserved |
| [templates](templates) | Teacher-supplied Elsevier bundle, numeric examples and documentation |
| [provenance](provenance) | Drive-source filenames, destinations, source links and SHA-256 hashes |

## Evidence boundaries

The active S1 profile excludes CT-07–CT-09 and numeric financial outputs because the exact dated regional GPU-hour price was not independently archived. The original S1 code and older price-bearing workbooks are retained in `archive/` for traceability. They must not be used to describe nine supported S1 paper checks or verified cheapest-system results.

S1 energy values use the declared cross-study 6.26-kW eight-H100 proxy, node scaling and PUE assumptions; they are not measured energy for the submitted Dell/HPE/Oracle systems. S2 makes no operational-energy or purchase-price optimization claim. Prototype rules and hardware tables include estimates and heterogeneous schemas and are not an operational recommendation engine.

See [docs/ARTIFACT_SCOPE.md](docs/ARTIFACT_SCOPE.md) for the paper-profile adjustments and [provenance/inclusion_notes.md](provenance/inclusion_notes.md) for source selection.

## Run one scenario

```bash
python experiments/s1/simulate_s1.py
python experiments/s2/s2_simulation.py --throughput 20000 --max-accelerators 8
python experiments/s2/s2_simulation.py --throughput 20000 --max-accelerators 2
```

The two S2 examples should respectively select `HPE-H100-8` and return `Infeasible`.

To regenerate performance figures, install the optional packages in `requirements-figures.txt`, then run:

```bash
python scripts/generate_s1_figures.py
python experiments/s2/generate_s2_figures.py
```

## Paper and format

The format is **Elsevier elsarticle**, numeric references, **3p single column, 12 pt**. It uses `\documentclass[final,3p,12pt,nopreprintline]{elsarticle}`. Compile [paper/main.tex](paper/main.tex) with pdfLaTeX. The matching working PDF is [paper/CCN_Final_Paper.pdf](paper/CCN_Final_Paper.pdf). The original template's numerical example is [templates/elsarticle/elsarticle-template-num.tex](templates/elsarticle/elsarticle-template-num.tex), and its 3p layout example is [templates/elsarticle/doc/elstest-3p.pdf](templates/elsarticle/doc/elstest-3p.pdf).

This is a working manuscript. Its requested author/header/section changes were applied in the supplied paper, while remaining body-language issues and the data-availability placeholder were retained. Insert this repository's URL or a commit-specific URL into the **Data and Code Availability** section when preparing the final submission.

## Sources and reuse

Official benchmark sources are linked at field level in the inputs and in [references/benchmark_source_index.csv](references/benchmark_source_index.csv). Publisher research PDFs are referenced through the bibliography and literature matrix rather than mirrored. Upstream notices in the Elsevier template are retained; no new blanket license is assigned to the collected third-party materials. Private editing links, internal planning access links, Word conversion internals and language-review documents are not part of this public artifact.
