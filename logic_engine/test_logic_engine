import unittest

from src.error_handlers import ErrorManager
from src.logic_engine import (
    CompositePipeline,
    ComprehensiveMetricsProcessor,
    ConfigManager,
    ThresholdFilterProcessor,
)


class TestLogicEngineSubsystem(unittest.TestCase):

    def setUp(self):
        self.config_mgr = ConfigManager()
        self.config_mgr.set_config(self.config_mgr.DEFAULT_CONFIG.copy())
        
        self.filter_stage = ThresholdFilterProcessor()
        self.filter_stage.initialize_processor(self.config_mgr)
        
        self.math_stage = ComprehensiveMetricsProcessor()
        self.math_stage.initialize_processor(self.config_mgr)
        
        self.sample_data = [
            {"asset_id": "HVAC_1", "timestamp": "2026-11-07 15:00:00", "energy_kwh": 60.0, "price": 0.15, "solar_kwh": 10.0},
            {"asset_id": "Base_1", "timestamp": "2026-11-07 15:00:00", "energy_kwh": 0.005, "price": 0.15, "solar_kwh": 10.0}, # Below threshold
            {"asset_id": "HVAC_1", "timestamp": "2026-11-07 02:00:00", "energy_kwh": 20.0, "price": 0.10, "solar_kwh": 0.0}
        ]

    # ==========================================
    # Configuration Tests (Tests 1-3)
    # ==========================================
    def test_01_config_loads_defaults_when_file_missing(self):
        """Ensure system doesn't crash if config.json is deleted."""
        self.config_mgr.initialize_config("fake_path.json")
        self.assertEqual(self.config_mgr.get_config()["baseline_energy_kwh"], 500.0)

    def test_02_config_overwrites_defaults_correctly(self):
        """Ensure dictionary merging works if user changes a value."""
        self.config_mgr.set_config({"baseline_energy_kwh": 999.0})
        self.assertEqual(self.config_mgr.get_config()["baseline_energy_kwh"], 999.0)

    def test_03_config_encapsulation_enforced(self):
        """Ensure get_config() properly returns dict (Testing OOP Encapsulation)."""
        self.assertIsInstance(self.config_mgr.get_config(), dict)

    # ==========================================
    # Filter Processor Tests (Tests 4-6)
    # ==========================================
    def test_04_filter_removes_inactive_readings(self):
        """Ensure rows below active_threshold_kwh are dropped."""
        filtered_data = self.filter_stage.process(self.sample_data)
        # Should drop the 0.005 row because default threshold is 0.01
        self.assertEqual(len(filtered_data), 2)

    def test_05_filter_handles_empty_stream(self):
        """Ensure filter safely returns empty list if DB is empty."""
        self.assertEqual(self.filter_stage.process([]), [])

    def test_06_filter_handles_missing_energy_key(self):
        """Ensure dict.get() prevents KeyError if 'energy_kwh' column is missing."""
        bad_data = [{"asset_id": "Bad_Meter", "timestamp": "2026-11-07 12:00:00"}] # No energy key
        filtered = self.filter_stage.process(bad_data)
        self.assertEqual(len(filtered), 0)

    # ==========================================
    # Math Processor Edge-Cases (Tests 7-12)
    # ==========================================
    def test_07_math_calculates_total_cost_correctly(self):
        """Cost = Energy * Price."""
        metrics = self.math_stage.process([self.sample_data[0]]) 
        # 60.0 kWh * $0.15 = $9.00
        self.assertEqual(metrics["total_cost_usd"], 9.00)

    def test_08_math_applies_peak_carbon_intensity(self):
        """Ensure 15:00 (3 PM) triggers the higher 0.450 peak carbon factor."""
        metrics = self.math_stage.process([self.sample_data[0]]) 
        # 60.0 kWh * 0.450 = 27.0 kg
        self.assertEqual(metrics["total_carbon_kg"], 27.0)

    def test_09_math_applies_offpeak_carbon_intensity(self):
        """Ensure 02:00 (2 AM) triggers the lower 0.300 off-peak carbon factor."""
        metrics = self.math_stage.process([self.sample_data[2]]) 
        # 20.0 kWh * 0.300 = 6.0 kg
        self.assertEqual(metrics["total_carbon_kg"], 6.0)

    def test_10_math_caps_sustainability_score(self):
        """Score should never exceed 100 even if usage is near zero."""
        tiny_usage = [{"asset_id": "1", "timestamp": "2026-11-07 12:00:00", "energy_kwh": 0.1, "price": 0.1}]
        metrics = self.math_stage.process(tiny_usage)
        self.assertEqual(metrics["sustainability_score"], 100.0)

    def test_11_math_detects_peak_demand_spikes(self):
        """Any usage > 50.0 kW should be logged in the peak_demands list."""
        metrics = self.math_stage.process([self.sample_data[0]]) 
        self.assertEqual(len(metrics["peak_demands_detected"]), 1)
        self.assertEqual(metrics["peak_demands_detected"][0]["val"], 60.0)

    def test_12_math_fills_missing_null_values(self):
        """NFR: Resilience. Missing prices should become 0.0, not crash the system."""
        null_data = [{"asset_id": "1", "timestamp": "2026-11-07 12:00:00", "energy_kwh": 10.0}] # Missing price
        metrics = self.math_stage.process(null_data)
        self.assertEqual(metrics["total_cost_usd"], 0.0)

    # ==========================================
    # Pipeline & Error Manager (Tests 13-15)
    # ==========================================
    def test_13_composite_pipeline_chains_correctly(self):
        """Test operator overloading (|) chains processors and shares data."""
        pipeline = self.filter_stage | self.math_stage
        self.assertIsInstance(pipeline, CompositePipeline)
        
        metrics = pipeline.process(self.sample_data)
        # Should drop the 1 inactive row, and calculate math on the remaining 2
        self.assertEqual(metrics["total_energy_kwh"], 80.0) # 60 + 20

    def test_14_error_manager_returns_safe_fallback(self):
        """Ensure ErrorManager returns a safe dictionary instead of crashing."""
        err_mgr = ErrorManager(log_filepath="test_errors.log")
        try:
            raise ValueError("Simulated division by zero")
        except Exception as e:
            safe_dict = err_mgr.handle_exception(e, "Test Context")
            
        self.assertEqual(safe_dict["status"], "FAILED")
        self.assertEqual(safe_dict["total_cost_usd"], 0.0)

    def test_15_math_groups_category_breakdown_correctly(self):
        """Ensure asset_ids are properly grouped dynamically."""
        data = [
            {"asset_id": "HVAC", "timestamp": "2026-01-01 12:00:00", "energy_kwh": 10.0},
            {"asset_id": "HVAC", "timestamp": "2026-01-01 13:00:00", "energy_kwh": 15.0},
            {"asset_id": "LIGHT", "timestamp": "2026-01-01 13:00:00", "energy_kwh": 5.0}
        ]
        metrics = self.math_stage.process(data)
        self.assertEqual(metrics["category_breakdown_kwh"]["HVAC"], 25.0)
        self.assertEqual(metrics["category_breakdown_kwh"]["LIGHT"], 5.0)

if __name__ == '__main__':
    unittest.main()
