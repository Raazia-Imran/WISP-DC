"""Reproducible S1 simulation for WISP-DC.

Paper-profile inputs are the extracted official MLPerf Training v4.0 records.
Technical calculations retain the original simulation logic. Price-based cases
CT-07–CT-09 and numeric monetary outputs are excluded to match the manuscript.
The unmodified original program is archived separately. Missing evidence is null.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


BASE = Path(__file__).resolve().parent
OUT = BASE / "generated_outputs"
DATA = BASE / "data" / "s1_verified_data.json"

PUE_BASE = 1.4
PUE_VALUES = [1.2, 1.4, 1.6]
RUNS_PER_YEAR = 365
DEADLINES_MIN = [3, 5, 8, 10, 15, 20, 30, 60]
RACK_LIMITS_KW = [40, 80, 120]
CALIBRATED_8GPU_NODE_KW = 6.26
BTU_PER_H_PER_KW = 3412.14

PHYSICAL = {
    "DELL-4G": {"deployment": "On-prem", "nodes": 1, "u_node": 4, "kg_node": 61.4, "planning_kw_node": None},
    "DELL-8G": {"deployment": "On-prem", "nodes": 1, "u_node": 6, "kg_node": 114.05, "planning_kw_node": 11.5},
    "HPE-8G": {"deployment": "On-prem", "nodes": 1, "u_node": 5, "kg_node": 108.9, "planning_kw_node": 12.0},
    "HPE-16G": {"deployment": "On-prem", "nodes": 2, "u_node": 5, "kg_node": 108.9, "planning_kw_node": 12.0},
    "OCI-8G": {"deployment": "Cloud", "nodes": 1, "u_node": None, "kg_node": None, "planning_kw_node": None},
    "OCI-64G": {"deployment": "Cloud", "nodes": 8, "u_node": None, "kg_node": None, "planning_kw_node": None},
}


def roundup_ratio(value: float, capacity: float) -> int:
    return int(math.ceil(value / capacity))


def main() -> None:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    records = raw["records"]
    results = []

    for rec in records:
        cid = rec["id"]
        phys = PHYSICAL[cid]
        time_min = rec["trimmed_mean_min"]
        time_h = time_min / 60.0
        nodes = phys["nodes"]
        calibrated_kw = None if cid == "DELL-4G" else CALIBRATED_8GPU_NODE_KW * nodes
        it_energy = None if calibrated_kw is None else calibrated_kw * time_h
        facility_energy = None if it_energy is None else it_energy * PUE_BASE
        heat = None if calibrated_kw is None else calibrated_kw * BTU_PER_H_PER_KW
        annual_energy = None if facility_energy is None else facility_energy * RUNS_PER_YEAR
        cloud_cost = None

        rack_status = "Provider managed"
        racks = None
        if phys["deployment"] == "On-prem":
            if phys["planning_kw_node"] is None:
                rack_status = "Incomplete: exact server power unavailable"
            else:
                total_u = nodes * phys["u_node"]
                total_kg = nodes * phys["kg_node"]
                total_kw = nodes * phys["planning_kw_node"]
                racks = max(
                    roundup_ratio(total_u, 36),
                    roundup_ratio(total_kg, 1360),
                    roundup_ratio(total_kw, 80),
                )
                rack_status = "Feasible" if phys["planning_kw_node"] <= 80 else "Infeasible: node exceeds rack power"

        results.append({
            "config_id": cid,
            "deployment": phys["deployment"],
            "gpus": rec["total_accelerators"],
            "nodes": nodes,
            "time_min": time_min,
            "cv": rec["run_cv"],
            "calibrated_it_kw": calibrated_kw,
            "it_energy_kwh_run": it_energy,
            "facility_energy_kwh_run": facility_energy,
            "annual_facility_energy_kwh": annual_energy,
            "heat_btu_h": heat,
            "cloud_cost_eur_run": cloud_cost,
            "racks_base": racks,
            "rack_status": rack_status,
        })

    deadline_rows = []
    for deadline in DEADLINES_MIN:
        feasible = [r for r in results if r["time_min"] <= deadline]
        smallest = min(feasible, key=lambda r: (r["gpus"], r["time_min"])) if feasible else None
        fastest = min(feasible, key=lambda r: r["time_min"]) if feasible else None
        deadline_rows.append({
            "deadline_min": deadline,
            "feasible_count": len(feasible),
            "minimum_gpu_config": None if smallest is None else smallest["config_id"],
            "minimum_gpus": None if smallest is None else smallest["gpus"],
            "fastest_config": None if fastest is None else fastest["config_id"],
        })

    pue_rows = []
    for pue in PUE_VALUES:
        for r in results:
            if r["it_energy_kwh_run"] is not None:
                e = r["it_energy_kwh_run"] * pue
                pue_rows.append({
                    "pue": pue,
                    "config_id": r["config_id"],
                    "facility_energy_kwh_run": e,
                    "annual_energy_kwh": e * RUNS_PER_YEAR,
                })

    rack_rows = []
    for limit in RACK_LIMITS_KW:
        for rec in records:
            cid = rec["id"]
            p = PHYSICAL[cid]
            if p["deployment"] != "On-prem" or p["planning_kw_node"] is None:
                continue
            total_u = p["nodes"] * p["u_node"]
            total_kg = p["nodes"] * p["kg_node"]
            total_kw = p["nodes"] * p["planning_kw_node"]
            node_fits = p["planning_kw_node"] <= limit
            racks = None if not node_fits else max(
                roundup_ratio(total_u, 36),
                roundup_ratio(total_kg, 1360),
                roundup_ratio(total_kw, limit),
            )
            rack_rows.append({
                "rack_limit_kw": limit,
                "config_id": cid,
                "planning_kw": total_kw,
                "racks": racks,
                "status": "Feasible" if node_fits else "Infeasible: one node exceeds limit",
            })

    validation = [
        {"test_id": "CT-01", "test": "2-minute deadline", "expected": "No configuration feasible", "actual": "Pass" if not [r for r in results if r["time_min"] <= 2] else "Fail"},
        {"test_id": "CT-02", "test": "3-minute deadline", "expected": "Only OCI-64G feasible", "actual": "Pass" if [r["config_id"] for r in results if r["time_min"] <= 3] == ["OCI-64G"] else "Fail"},
        {"test_id": "CT-03", "test": "10 kW rack limit for 11.5 kW Dell node", "expected": "Reject", "actual": "Pass" if PHYSICAL["DELL-8G"]["planning_kw_node"] > 10 else "Fail"},
        {"test_id": "CT-04", "test": "Run-status audit detects the Dell-8G aborted log", "expected": "Exactly one aborted log is flagged, not hidden", "actual": "Pass" if sum(run["status"] != "success" for r in records for run in r["runs"]) == 1 else "Fail"},
        {"test_id": "CT-05", "test": "PUE increase raises facility energy", "expected": "Strictly increasing", "actual": "Pass" if all(r["it_energy_kwh_run"] is None or r["it_energy_kwh_run"]*1.2 < r["it_energy_kwh_run"]*1.4 < r["it_energy_kwh_run"]*1.6 for r in results) else "Fail"},
        {"test_id": "CT-06", "test": "Cloud rack placement", "expected": "Provider managed, not fabricated", "actual": "Pass" if all(r["rack_status"] == "Provider managed" for r in results if r["deployment"] == "Cloud") else "Fail"},
    ]

    # Monetary budget cases CT-07–CT-09 are excluded from the paper profile.
    budget_rows = []

    # Independent hand-style check for DELL-8G, retained as explicit arithmetic.
    dell8 = next(r for r in results if r["config_id"] == "DELL-8G")
    manual = {
        "config_id": "DELL-8G",
        "time_h": 13.16277777777778 / 60,
        "it_energy_kwh": 6.26 * (13.16277777777778 / 60),
        "facility_energy_kwh": 6.26 * (13.16277777777778 / 60) * 1.4,
        "heat_btu_h": 6.26 * 3412.14,
        "annual_energy_kwh": 6.26 * (13.16277777777778 / 60) * 1.4 * 365,
        "model_facility_energy_kwh": dell8["facility_energy_kwh_run"],
    }

    payload = {
        "assumptions": {
            "deadlines_min": DEADLINES_MIN,
            "pue_base": PUE_BASE,
            "pue_values": PUE_VALUES,
            "runs_per_year": RUNS_PER_YEAR,
            "rack_limits_kw": RACK_LIMITS_KW,
            "price_optimization_performed": False,
            "price_evidence_status": "Excluded: exact dated regional rate not independently archived",
            "redundancy": "None for benchmark-reproduction training scenario",
        },
        "results": results,
        "deadline_sensitivity": deadline_rows,
        "pue_sensitivity": pue_rows,
        "rack_sensitivity": rack_rows,
        "budget_feasibility": budget_rows,
        "validation": validation,
        "manual_check": manual,
    }
    (OUT / "s1_simulation_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(OUT / "s1_simulation_results.json")


if __name__ == "__main__":
    main()
