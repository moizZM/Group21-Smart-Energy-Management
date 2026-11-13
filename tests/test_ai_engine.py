"""
Automated Unit Tests (Hometask 4)
"""

import os
import unittest
from unittest.mock import patch

# Use the same data package setup as the Flask API.
from database_reader import DatabaseManager
from src.assets.battery import Battery

from ai_engine.optimizer import AlEngine, EnergyAdvisor, Summarizer, SubsystemStatus
from logic_engine.logic_engine import ConfigManager


class TestSEMSCompleteSuite(unittest.TestCase):

    def test_01_battery_soc(self) -> None:
        b = Battery("b1", "Test BESS", 10.0, stored_kwh=5.0)
        self.assertAlmostEqual(b.state_of_charge_percent, 50.0)

    def test_02_battery_charge(self) -> None:
        b = Battery("b1", "Test BESS", 10.0, stored_kwh=5.0)
        b.charge(4.0)
        self.assertGreater(b.state_of_charge_percent, 50.0)

    def test_03_config_manager(self) -> None:
        cfg = ConfigManager()
        cfg.initialize_config()
        self.assertIn("active_threshold_kwh", cfg.get_config())

    def test_04_ai_engine_init(self) -> None:
        engine = AlEngine(101)
        self.assertEqual(engine.initialize(), SubsystemStatus.RUNNING)

    def test_05_advisor_recommendation(self) -> None:
        advisor = EnergyAdvisor(102, 0.30)
        action = advisor.recommend_battery_action(0.38, 0.2)
        self.assertEqual(action, "DISCHARGE")

    def test_06_summarizer_report(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            sum_obj = Summarizer(103)
        report = sum_obj.generate_sustainability_coach_report(
            {"total_cost_usd": 15.0, "sustainability_score": 85.0}
        )
        self.assertIn("AI Sustainability Coach", report)

    def test_07_database_init(self) -> None:
        with DatabaseManager(":memory:") as db:
            self.assertTrue(db.get_readings().empty)


if __name__ == "__main__":
    unittest.main()
