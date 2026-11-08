@echo off
echo Running all S2 scenarios and sensitivity cases...
python s2_simulation.py --run-all
echo.
echo Running the automated validation suite...
python -m unittest -v test_s2_simulation.py
echo.
echo Example: 20,000 output tokens/s with at most 8 accelerators
python s2_simulation.py --throughput 20000 --max-accelerators 8
pause
