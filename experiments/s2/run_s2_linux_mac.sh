#!/usr/bin/env sh
set -eu
python3 s2_simulation.py --run-all
python3 -m unittest -v test_s2_simulation.py
python3 s2_simulation.py --throughput 20000 --max-accelerators 8
