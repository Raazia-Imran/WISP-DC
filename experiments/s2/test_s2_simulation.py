"""Automated validation suite for the WISP-DC S2 simulation."""

from __future__ import annotations

import math
import unittest

from s2_simulation import Requirement, evaluate_configuration, load_configurations, load_test_cases, recommend


class S2SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = load_configurations()

    def req(self, throughput=20_000, max_accelerators=8, ttft=2.0, tpot=0.2,
            rouge1=43.986888, rouge2=21.814848, rougeL=28.330038):
        return Requirement("TEST", throughput, max_accelerators, ttft, tpot, rouge1, rouge2, rougeL)

    def test_01_four_official_configurations_loaded(self):
        self.assertEqual(len(self.configs), 4)

    def test_02_official_throughput_values_reconciled(self):
        observed = {c.config_id: c.output_tokens_per_s for c in self.configs}
        expected = {
            "HPE-GH200-1": 4327.68,
            "HPE-GH200-2": 8674.58,
            "HPE-H100-8": 30498.87,
            "HPE-H200-8": 31281.09,
        }
        self.assertEqual(observed, expected)

    def test_03_all_results_marked_valid(self):
        self.assertTrue(all(c.result == "VALID" for c in self.configs))

    def test_04_all_pass_official_latency_and_accuracy(self):
        req = self.req(throughput=1, max_accelerators=8)
        for config in self.configs:
            row = evaluate_configuration(config, req)
            self.assertTrue(row["checks"]["ttft"])
            self.assertTrue(row["checks"]["tpot"])
            self.assertTrue(row["checks"]["rouge1"])
            self.assertTrue(row["checks"]["rouge2"])
            self.assertTrue(row["checks"]["rougeL"])

    def test_05_all_six_cases_match_workbook(self):
        for req, expected_rec, expected_status in load_test_cases():
            result = recommend(self.configs, req)
            self.assertEqual(result["recommendation"], expected_rec, req.case_id)
            self.assertEqual(result["status"], expected_status, req.case_id)

    def test_06_t3_is_infeasible_due_to_throughput_and_budget_conflict(self):
        result = recommend(self.configs, self.req(20_000, 2))
        self.assertEqual(result["status"], "Infeasible")
        self.assertEqual(result["recommendation"], "None")

    def test_07_t4_relaxing_accelerator_limit_restores_feasibility(self):
        result = recommend(self.configs, self.req(20_000, 8))
        self.assertEqual(result["recommendation"], "HPE-H100-8")
        self.assertEqual(result["feasible_configurations"], ["HPE-H100-8", "HPE-H200-8"])

    def test_08_equal_count_tie_uses_minimum_excess_throughput(self):
        result = recommend(self.configs, self.req(30_000, 8))
        self.assertEqual(result["recommendation"], "HPE-H100-8")

    def test_09_h200_selected_when_h100_misses_requirement(self):
        result = recommend(self.configs, self.req(31_000, 8))
        self.assertEqual(result["recommendation"], "HPE-H200-8")

    def test_10_requirement_above_all_measured_results_is_infeasible(self):
        result = recommend(self.configs, self.req(32_000, 8))
        self.assertEqual(result["status"], "Infeasible")

    def test_11_strict_ttft_can_reject_all_configurations(self):
        result = recommend(self.configs, self.req(4_000, 8, ttft=0.5))
        self.assertEqual(result["status"], "Infeasible")

    def test_12_strict_tpot_can_reject_all_configurations(self):
        result = recommend(self.configs, self.req(4_000, 8, tpot=0.1))
        self.assertEqual(result["status"], "Infeasible")

    def test_13_strict_accuracy_can_reject_all_configurations(self):
        result = recommend(self.configs, self.req(4_000, 8, rouge1=50.0))
        self.assertEqual(result["status"], "Infeasible")

    def test_14_manual_tokens_per_accelerator_check(self):
        gh200_2 = next(c for c in self.configs if c.config_id == "HPE-GH200-2")
        self.assertTrue(math.isclose(gh200_2.output_tokens_per_s / gh200_2.accelerators, 4337.29, abs_tol=1e-9))

    def test_15_manual_latency_margin_check(self):
        gh200_1 = next(c for c in self.configs if c.config_id == "HPE-GH200-1")
        row = evaluate_configuration(gh200_1, self.req(4_000, 1))
        self.assertTrue(math.isclose(row["ttft_margin_s"], 0.110535687, abs_tol=1e-12))
        self.assertTrue(math.isclose(row["tpot_margin_s"], 0.00910549, abs_tol=1e-12))

    def test_16_price_optimization_is_explicitly_false(self):
        result = recommend(self.configs, self.req(4_000, 1))
        self.assertFalse(result["price_optimization_performed"])

    def test_17_invalid_nonpositive_throughput_rejected(self):
        with self.assertRaises(ValueError):
            recommend(self.configs, self.req(0, 8))

    def test_18_invalid_nonpositive_accelerator_limit_rejected(self):
        with self.assertRaises(ValueError):
            recommend(self.configs, self.req(4_000, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
