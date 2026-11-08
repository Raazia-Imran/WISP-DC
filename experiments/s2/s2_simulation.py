"""WISP-DC S2: reproducible AI-inference infrastructure-feasibility simulation.

This program does not run Llama 2 70B inference locally. It consumes official
MLPerf Inference v5.0 measurements and evaluates user-supplied infrastructure
requirements against those measured configurations.

Decision rule:
1. Reject any configuration that is not a VALID MLPerf result.
2. Enforce throughput, accelerator-count, TTFT, TPOT, and ROUGE thresholds.
3. Among feasible configurations, minimize accelerator count.
4. If accelerator counts tie, minimize excess throughput (right-sizing).
5. If still tied, use config_id only as a deterministic final ordering.

No monetary price, operational energy, CAPEX, TCO, or ROI is inferred because
the selected submissions do not provide comparable prices or matched whole-
server power measurements.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PACKAGE_DIR = Path(__file__).resolve().parent
BENCHMARK_CSV = PACKAGE_DIR / "s2_benchmark_data.csv"
CASES_CSV = PACKAGE_DIR / "s2_test_cases.csv"
OUTPUT_DIR = PACKAGE_DIR / "generated_outputs"


@dataclass(frozen=True)
class Configuration:
    config_id: str
    submission_id: str
    submitter: str
    system: str
    model: str
    dataset: str
    scenario: str
    accuracy_target: str
    nodes: int
    accelerators: int
    accelerator: str
    memory_per_accelerator_gb: float
    output_tokens_per_s: float
    samples_per_s: float
    p99_ttft_s: float
    ttft_limit_s: float
    p99_tpot_s: float
    tpot_limit_s: float
    result: str
    rouge1: float
    rouge2: float
    rougeL: float
    rouge1_threshold: float
    rouge2_threshold: float
    rougeL_threshold: float
    performance_log_url: str
    accuracy_url: str
    system_json_url: str


@dataclass(frozen=True)
class Requirement:
    case_id: str
    required_output_tokens_per_s: float
    max_accelerators: int
    max_ttft_s: float
    max_tpot_s: float
    required_rouge1: float
    required_rouge2: float
    required_rougeL: float


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def load_configurations(path: Path = BENCHMARK_CSV) -> list[Configuration]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        Configuration(
            config_id=r["config_id"], submission_id=r["submission_id"],
            submitter=r["submitter"], system=r["system"], model=r["model"],
            dataset=r["dataset"], scenario=r["scenario"],
            accuracy_target=r["accuracy_target"], nodes=_int(r, "nodes"),
            accelerators=_int(r, "accelerators"), accelerator=r["accelerator"],
            memory_per_accelerator_gb=_float(r, "memory_per_accelerator_gb"),
            output_tokens_per_s=_float(r, "output_tokens_per_s"),
            samples_per_s=_float(r, "samples_per_s"),
            p99_ttft_s=_float(r, "p99_ttft_s"), ttft_limit_s=_float(r, "ttft_limit_s"),
            p99_tpot_s=_float(r, "p99_tpot_s"), tpot_limit_s=_float(r, "tpot_limit_s"),
            result=r["result"], rouge1=_float(r, "rouge1"),
            rouge2=_float(r, "rouge2"), rougeL=_float(r, "rougeL"),
            rouge1_threshold=_float(r, "rouge1_threshold"),
            rouge2_threshold=_float(r, "rouge2_threshold"),
            rougeL_threshold=_float(r, "rougeL_threshold"),
            performance_log_url=r["performance_log_url"], accuracy_url=r["accuracy_url"],
            system_json_url=r["system_json_url"],
        )
        for r in rows
    ]


def load_test_cases(path: Path = CASES_CSV) -> list[tuple[Requirement, str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = []
    for r in rows:
        req = Requirement(
            case_id=r["case_id"],
            required_output_tokens_per_s=_float(r, "required_output_tokens_per_s"),
            max_accelerators=_int(r, "max_accelerators"),
            max_ttft_s=_float(r, "max_ttft_s"),
            max_tpot_s=_float(r, "max_tpot_s"),
            required_rouge1=_float(r, "required_rouge1"),
            required_rouge2=_float(r, "required_rouge2"),
            required_rougeL=_float(r, "required_rougeL"),
        )
        result.append((req, r["expected_recommendation"], r["expected_status"]))
    return result


def evaluate_configuration(config: Configuration, req: Requirement) -> dict:
    checks = {
        "valid_result": config.result.upper() == "VALID",
        "throughput": config.output_tokens_per_s >= req.required_output_tokens_per_s,
        "accelerator_budget": config.accelerators <= req.max_accelerators,
        "ttft": config.p99_ttft_s <= req.max_ttft_s,
        "tpot": config.p99_tpot_s <= req.max_tpot_s,
        "rouge1": config.rouge1 >= req.required_rouge1,
        "rouge2": config.rouge2 >= req.required_rouge2,
        "rougeL": config.rougeL >= req.required_rougeL,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "config_id": config.config_id,
        "accelerators": config.accelerators,
        "output_tokens_per_s": config.output_tokens_per_s,
        "throughput_surplus_tokens_per_s": config.output_tokens_per_s - req.required_output_tokens_per_s,
        "p99_ttft_s": config.p99_ttft_s,
        "ttft_margin_s": req.max_ttft_s - config.p99_ttft_s,
        "p99_tpot_s": config.p99_tpot_s,
        "tpot_margin_s": req.max_tpot_s - config.p99_tpot_s,
        "checks": checks,
        "failed_checks": failed,
        "feasible": not failed,
    }


def recommend(configurations: Iterable[Configuration], req: Requirement) -> dict:
    if req.required_output_tokens_per_s <= 0:
        raise ValueError("required_output_tokens_per_s must be positive")
    if req.max_accelerators <= 0:
        raise ValueError("max_accelerators must be positive")
    if req.max_ttft_s <= 0 or req.max_tpot_s <= 0:
        raise ValueError("latency limits must be positive")

    evaluations = [evaluate_configuration(config, req) for config in configurations]
    feasible = [row for row in evaluations if row["feasible"]]
    feasible.sort(key=lambda row: (
        row["accelerators"],
        row["throughput_surplus_tokens_per_s"],
        row["config_id"],
    ))

    selected = feasible[0] if feasible else None
    if selected:
        status = "Feasible"
        recommendation = selected["config_id"]
        reason = (
            "Minimum accelerator count among evaluated configurations satisfying "
            "validity, throughput, accelerator, latency, and accuracy constraints; "
            "minimum excess throughput resolves equal-count ties."
        )
    else:
        status = "Infeasible"
        recommendation = "None"
        reason = "No evaluated configuration satisfies all hard constraints."

    return {
        "case_id": req.case_id,
        "requirement": asdict(req),
        "status": status,
        "recommendation": recommendation,
        "reason": reason,
        "feasible_configurations": [row["config_id"] for row in feasible],
        "evaluations": evaluations,
        "price_optimization_performed": False,
        "price_limitation": (
            "Comparable dated full-system prices are unavailable; this result is "
            "minimum-resource technical feasibility, not verified cheapest purchase price."
        ),
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_all(output_dir: Path = OUTPUT_DIR) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    configs = load_configurations()
    cases = load_test_cases()

    detailed_results = []
    summary_rows = []
    for req, expected_recommendation, expected_status in cases:
        result = recommend(configs, req)
        result["expected_recommendation"] = expected_recommendation
        result["expected_status"] = expected_status
        result["matches_expected"] = (
            result["recommendation"] == expected_recommendation
            and result["status"] == expected_status
        )
        detailed_results.append(result)
        summary_rows.append({
            "case_id": req.case_id,
            "required_output_tokens_per_s": req.required_output_tokens_per_s,
            "max_accelerators": req.max_accelerators,
            "recommendation": result["recommendation"],
            "status": result["status"],
            "expected_recommendation": expected_recommendation,
            "expected_status": expected_status,
            "matches_expected": result["matches_expected"],
            "feasible_configurations": ";".join(result["feasible_configurations"]),
            "selection_rule": "min accelerators, then min throughput surplus",
        })

    (output_dir / "s2_detailed_results.json").write_text(
        json.dumps(detailed_results, indent=2), encoding="utf-8"
    )
    write_csv(
        output_dir / "s2_scenario_results.csv",
        summary_rows,
        list(summary_rows[0].keys()),
    )

    sensitivity_rows = []
    for max_accelerators in (1, 2, 8):
        for required in range(2000, 34001, 1000):
            req = Requirement(
                case_id=f"SENS-{max_accelerators}-{required}",
                required_output_tokens_per_s=float(required),
                max_accelerators=max_accelerators,
                max_ttft_s=2.0,
                max_tpot_s=0.2,
                required_rouge1=43.986888,
                required_rouge2=21.814848,
                required_rougeL=28.330038,
            )
            result = recommend(configs, req)
            sensitivity_rows.append({
                "required_output_tokens_per_s": required,
                "max_accelerators": max_accelerators,
                "recommendation": result["recommendation"],
                "status": result["status"],
            })
    write_csv(
        output_dir / "s2_sensitivity_results.csv",
        sensitivity_rows,
        list(sensitivity_rows[0].keys()),
    )

    payload = {
        "scenario_count": len(summary_rows),
        "scenario_matches": sum(row["matches_expected"] for row in summary_rows),
        "all_scenarios_match_workbook": all(row["matches_expected"] for row in summary_rows),
        "sensitivity_rows": len(sensitivity_rows),
        "evidence_boundary": {
            "local_llama_inference_executed": False,
            "official_mlperf_traces_used": True,
            "operational_energy_claimed": False,
            "monetary_cheapest_claimed": False,
        },
    }
    (output_dir / "s2_run_manifest.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return payload


def build_requirement_from_args(args: argparse.Namespace) -> Requirement:
    return Requirement(
        case_id="USER",
        required_output_tokens_per_s=args.throughput,
        max_accelerators=args.max_accelerators,
        max_ttft_s=args.max_ttft,
        max_tpot_s=args.max_tpot,
        required_rouge1=args.rouge1,
        required_rouge2=args.rouge2,
        required_rougeL=args.rougeL,
    )


def print_result(result: dict) -> None:
    req = result["requirement"]
    print("WISP-DC S2 AI-Inference Feasibility Simulation")
    print(f"Input: throughput={req['required_output_tokens_per_s']:,.2f} output tokens/s, "
          f"max accelerators={req['max_accelerators']}, "
          f"TTFT≤{req['max_ttft_s']} s, TPOT≤{req['max_tpot_s']} s")
    print("\nConfiguration checks:")
    for row in result["evaluations"]:
        if row["feasible"]:
            detail = "PASS"
        else:
            detail = "FAIL: " + ", ".join(row["failed_checks"])
        print(f"  {row['config_id']:<13} {detail}")
    print(f"\nStatus: {result['status']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Reason: {result['reason']}")
    print("Cost note: no monetary cheapest-system claim was made.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-all", action="store_true", help="Generate all scenario and sensitivity outputs")
    parser.add_argument("--throughput", type=float, help="Required completed output tokens/s")
    parser.add_argument("--max-accelerators", type=int, help="Maximum accelerator count")
    parser.add_argument("--max-ttft", type=float, default=2.0, help="Maximum p99 TTFT in seconds")
    parser.add_argument("--max-tpot", type=float, default=0.2, help="Maximum p99 TPOT in seconds")
    parser.add_argument("--rouge1", type=float, default=43.986888)
    parser.add_argument("--rouge2", type=float, default=21.814848)
    parser.add_argument("--rougeL", type=float, default=28.330038)
    args = parser.parse_args()

    if args.run_all:
        manifest = run_all()
        print(json.dumps(manifest, indent=2))
        return
    if args.throughput is None or args.max_accelerators is None:
        parser.error("provide --run-all or both --throughput and --max-accelerators")
    result = recommend(load_configurations(), build_requirement_from_args(args))
    print_result(result)


if __name__ == "__main__":
    main()
