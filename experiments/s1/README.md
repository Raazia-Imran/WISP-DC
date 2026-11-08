# S1 paper profile

Run `python simulate_s1.py` here, or `python reproduce.py` at the repository root.

`data/s1_verified_data.json` contains six observed H100 configurations and thirty extracted raw-run records, with official source URLs, timestamps, status and accuracy fields. `generated_outputs/s1_simulation_results.json` contains technical results, the eight deadline cases, PUE/rack sensitivity, the six retained CT checks and a manual Dell-8G arithmetic example.

This profile excludes the three unverified price-dependent checks and numerical tariffs/costs. The original source code and original results are in `archive/s1_original/`. No local ResNet model is trained. The proxy-power boundary and other limitations are described in the root README and `docs/ARTIFACT_SCOPE.md`.
