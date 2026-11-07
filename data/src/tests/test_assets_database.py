import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.assets.battery import Battery
from src.assets.building import Building
from src.assets.energy_asset import AssetError
from src.assets.smart_appliance import SmartAppliance
from src.assets.solar_panel import SolarPanel
from src.data_base.data_import import DataImporter, DataImportError
from src.data_base.database_manager import DatabaseError, DatabaseManager
from src.data_base.records import Alert, SimulationResult
from src.data_base.validation import DataCleaner, DataValidationError


class AssetTests(unittest.TestCase):
    def test_battery_charge_and_discharge_respect_capacity(self):
        battery = Battery("battery-1", "Home battery", capacity_kwh=10, efficiency=0.8,
                          stored_kwh=9.6)

        accepted = battery.charge(1)
        delivered = battery.discharge(2)

        self.assertAlmostEqual(accepted, 0.5)
        self.assertEqual(battery.state_of_charge_percent, 80)
        self.assertEqual(delivered, 2)
        self.assertAlmostEqual(battery.stored_kwh, 8)

    def test_battery_rejects_negative_charge(self):
        battery = Battery("battery-1", "Battery", capacity_kwh=10)

        with self.assertRaises(AssetError):
            battery.charge(-1)

    def test_battery_capacity_cannot_be_less_than_stored_energy(self):
        battery = Battery("battery-1", "Battery", capacity_kwh=10, stored_kwh=5)

        with self.assertRaises(AssetError):
            battery.capacity_kwh = 4

        self.assertEqual(battery.capacity_kwh, 10)

    def test_asset_configuration_rolls_back_after_invalid_setting(self):
        battery = Battery("battery-1", "Battery", capacity_kwh=10, stored_kwh=5)

        with self.assertRaises(AssetError):
            battery.configure(name="Updated battery", capacity_kwh=4)

        self.assertEqual(battery.name, "Battery")
        self.assertEqual(battery.capacity_kwh, 10)

    def test_solar_panel_calculates_and_tracks_generation(self):
        panel = SolarPanel("solar-1", "Roof", area_m2=10, efficiency=0.2,
                           performance_ratio=0.8)

        self.assertAlmostEqual(panel.generation_kwh(0.1), 0.16)
        self.assertAlmostEqual(panel.last_generation_kwh, 0.16)

    def test_appliance_consumes_energy_only_when_on(self):
        appliance = SmartAppliance("appliance-1", "Heater", rated_power_kw=2)

        self.assertEqual(appliance.run(1), 0)
        appliance.turn_on()
        self.assertEqual(appliance.run(0.5), 1)
        self.assertEqual(appliance.total_kwh, 1)

    def test_building_balances_generation_demand_and_battery(self):
        building = Building("Home")
        building.register_asset(Battery("battery-1", "Battery", capacity_kwh=2, stored_kwh=0.5))
        building.register_asset(SolarPanel("solar-1", "Roof", area_m2=10))
        building.register_asset(
            SmartAppliance("appliance-1", "Heater", rated_power_kw=1, status=True)
        )

        result = building.simulate_step(hours=0.5, irradiance_kwh_m2=0.1)

        self.assertAlmostEqual(result["solar_kwh"], 0.16)
        self.assertAlmostEqual(result["appliance_kwh"], 0.5)
        self.assertAlmostEqual(result["battery_discharged_kwh"], 0.34)
        self.assertAlmostEqual(result["grid_import_kwh"], 0)
        self.assertAlmostEqual(result["grid_export_kwh"], 0)

    def test_building_rejects_duplicate_asset_ids(self):
        building = Building("Home")
        building.register_asset(Battery("asset-1", "Battery", capacity_kwh=10))

        with self.assertRaises(AssetError):
            building.register_asset(SolarPanel("asset-1", "Roof", area_m2=10))


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        db_path = Path(self.temp_dir.name) / "energy.db"
        self.db = DatabaseManager(str(db_path))
        self.addCleanup(self.db.close)

    def test_asset_round_trips_through_sqlite(self):
        battery = Battery("battery-1", "Home battery", capacity_kwh=10, stored_kwh=7.2)

        self.db.save_asset(battery)
        restored = self.db.load_asset("battery-1")

        self.assertIsInstance(restored, Battery)
        self.assertEqual(restored.name, "Home battery")
        self.assertEqual(restored.capacity_kwh, 10)
        self.assertEqual(restored.stored_kwh, 7.2)

    def test_loading_unknown_asset_raises_database_error(self):
        with self.assertRaises(DatabaseError):
            self.db.load_asset("missing-asset")

    def test_readings_insert_once_and_can_be_retrieved(self):
        readings = pd.DataFrame([
            {"asset_id": "meter-1", "timestamp": "2024-01-01 00:00:00", "energy_kwh": 1.25},
            {"asset_id": "meter-1", "timestamp": "2024-01-01 00:30:00", "energy_kwh": 0.75},
        ])

        self.assertEqual(self.db.add_readings(readings), 2)
        self.assertEqual(self.db.add_readings(readings), 0)
        restored = self.db.get_readings(asset_id="meter-1")
        self.assertEqual(len(restored), 2)
        self.assertAlmostEqual(restored["energy_kwh"].sum(), 2)

    def test_readings_filter_by_asset_and_time_range(self):
        readings = pd.DataFrame([
            {"asset_id": "meter-1", "timestamp": "2024-01-01 00:00:00", "energy_kwh": 1},
            {"asset_id": "meter-1", "timestamp": "2024-01-01 00:30:00", "energy_kwh": 2},
            {"asset_id": "meter-2", "timestamp": "2024-01-01 00:30:00", "energy_kwh": 4},
        ])
        self.db.add_readings(readings)

        selected = self.db.get_readings(
            asset_id="meter-1", start="2024-01-01 00:30:00", end="2024-01-01 01:00:00"
        )

        self.assertEqual(selected["energy_kwh"].tolist(), [2])

    def test_simulation_results_and_alerts_round_trip(self):
        self.db.save_asset(Battery("battery-1", "Home battery", capacity_kwh=10))
        result = SimulationResult("morning", {"grid_import_kwh": 1.5}, cost=0.3)
        alert = Alert("battery-1", "warning", "Battery charge is low")

        run_id = self.db.save_result(result)
        alert_id = self.db.add_alert(alert)

        restored_result = self.db.get_results("morning")[0]
        restored_alert = self.db.get_alerts(unacknowledged_only=True)[0]
        self.assertGreater(run_id, 0)
        self.assertEqual(restored_result.totals, {"grid_import_kwh": 1.5})
        self.assertEqual(restored_alert.alert_id, alert_id)
        self.assertEqual(restored_alert.message, "Battery charge is low")

        self.db.acknowledge_alert(alert_id)
        self.assertEqual(self.db.get_alerts(unacknowledged_only=True), [])

    def test_importer_cleans_and_saves_wide_csv(self):
        csv_path = Path(self.temp_dir.name) / "readings.csv"
        csv_path.write_text(
            "time,load_a,load_b,usd_kwh\n"
            "2024-01-01 00:00:00,1,3,0.2\n"
            "2024-01-01 00:30:00,2,100,0.3\n",
            encoding="utf-8",
        )
        config = {
            "columns": {"timestamp": "time", "price": "usd_kwh"},
            "required": ["timestamp", "energy_kwh"],
            "default_asset_id": "home",
            "limits": {"energy_kwh": [0, 10], "price": [-1, 10]},
            "wide_format": {
                "meters": {"meter_a": "load_a", "meter_b": "load_b"},
                "derived_total": "home_total",
                "context": {"price": "price"},
            },
        }
        importer = DataImporter(config)

        report = importer.import_into(str(csv_path), self.db)

        self.assertEqual(report.layout, "wide")
        self.assertEqual(report.rows_in, 6)
        self.assertEqual(report.invalid_readings, 2)
        self.assertEqual(report.rows_saved, 4)
        self.assertEqual(report.rows_stored_new, 4)
        self.assertEqual(len(self.db.get_readings()), 4)
        self.assertEqual(importer.import_into(str(csv_path), self.db).rows_stored_new, 0)

    def test_importer_reports_missing_input_file(self):
        missing_path = Path(self.temp_dir.name) / "missing.csv"

        with self.assertRaises(DataImportError):
            DataImporter.read_table(str(missing_path))

    def test_importer_reports_unsupported_file_type(self):
        unsupported_path = Path(self.temp_dir.name) / "readings.txt"
        unsupported_path.write_text("not a supported table", encoding="utf-8")

        with self.assertRaises(DataImportError):
            DataImporter.read_table(str(unsupported_path))

    def test_importer_reports_missing_required_column(self):
        csv_path = Path(self.temp_dir.name) / "missing_energy.csv"
        csv_path.write_text("timestamp,value\n2024-01-01 00:00:00,1\n", encoding="utf-8")
        importer = DataImporter({"required": ["timestamp", "energy_kwh"]})

        with self.assertRaises(DataValidationError):
            importer.import_into(str(csv_path), self.db)

    def test_cleaner_drops_invalid_timestamps_and_duplicate_rows(self):
        readings = pd.DataFrame([
            {"asset_id": "meter-1", "timestamp": "2024-01-01 00:00:00", "energy_kwh": 1},
            {"asset_id": "meter-1", "timestamp": "2024-01-01 00:00:00", "energy_kwh": 1},
            {"asset_id": "meter-1", "timestamp": "not-a-date", "energy_kwh": 2},
        ])

        cleaned, report = DataCleaner().clean(readings)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(report.bad_timestamps, 1)
        self.assertEqual(report.duplicates, 1)


if __name__ == "__main__":
    unittest.main()
