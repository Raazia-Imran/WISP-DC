"""Replay the paper's S1/S2 cases and retain the 24 supported automated checks."""
from pathlib import Path
import csv
import json
import subprocess
import sys
import platform
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

def main():
    subprocess.run([sys.executable, 'simulate_s1.py'], cwd=ROOT/'experiments/s1', check=True)
    subprocess.run([sys.executable, 's2_simulation.py', '--run-all'], cwd=ROOT/'experiments/s2', check=True)
    tests = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'test_s2_simulation.py'],
                           cwd=ROOT/'experiments/s2', capture_output=True, text=True)
    out = ROOT/'validation'; out.mkdir(exist_ok=True)
    (out/'s2_unittest.txt').write_text(tests.stdout + tests.stderr, encoding='utf-8')
    print(tests.stdout + tests.stderr)
    if tests.returncode:
        raise SystemExit(tests.returncode)
    s1 = json.loads((ROOT/'experiments/s1/generated_outputs/s1_simulation_results.json').read_text())
    retained = s1['validation']
    if len(retained) != 6 or any(t['actual'] != 'Pass' for t in retained):
        raise AssertionError('The six retained S1 validation checks did not all pass')
    expected = ['OCI-64G','OCI-64G','HPE-16G','HPE-16G','DELL-8G','DELL-8G','DELL-4G','DELL-4G']
    if [r['minimum_gpu_config'] for r in s1['deadline_sensitivity']] != expected:
        raise AssertionError('S1 deadline recommendations differ from the paper')
    if s1['budget_feasibility'] or any(r['cloud_cost_eur_run'] is not None for r in s1['results']):
        raise AssertionError('Excluded price assumptions leaked into the paper profile')
    s2 = json.loads((ROOT/'experiments/s2/generated_outputs/s2_run_manifest.json').read_text())
    if not (s2['scenario_count'] == s2['scenario_matches'] == 6 and s2['sensitivity_rows'] == 99):
        raise AssertionError('S2 case or sensitivity coverage differs from the paper')
    result = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(),
        's1_retained_checks': 6, 's1_passed': 6,
        's2_unittest_checks': 18, 's2_passed': 18,
        'total_supported_checks': 24,
        's1_deadline_cases': 8, 's2_expected_cases_matched': 6, 's2_sensitivity_cases': 99,
        's1_excluded_price_cases': ['CT-07','CT-08','CT-09'],
        'numeric_price_optimization_performed': False,
        'local_resnet_training_executed': False, 'local_llama_inference_executed': False,
        'scope': 'Offline replay of supplied benchmark extracts; no independent physical measurement.',
    }
    (out/'reproduction_summary.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    (out/'s1_retained_checks.json').write_text(json.dumps(retained, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
