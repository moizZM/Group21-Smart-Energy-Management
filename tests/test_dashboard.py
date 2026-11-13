import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from dashboard import DashboardData, EnergyChart, EnergyDashboard
from dashboard.errors import DashboardError


class DashboardTests(unittest.TestCase):

    def setUp(self):
        # Two readings on the first day and one on the second day.
        self.readings = pd.DataFrame({
            "date": [
                "01/01/2020 00:00",
                "01/01/2020 00:30",
                "01/02/2020 00:00",
            ],
            "base_load_kwh": [1.0, 0.5, 2.0],
            "hvac_load_kwh": [2.0, 1.0, 0.0],
            "washing_machine_kwh": [0.5, 0.0, 1.0],
            "dishwasher_kwh": [0.25, 0.25, 0.0],
            "pv_energy_kwh": [0.4, 0.6, 1.5],
        })

        self.data = DashboardData()
        self.data.set_readings(self.readings)

    def test_daily_totals_use_interval_energy(self):
        totals = self.data.get_daily_totals("2020-01-01")

        # The readings are already kWh, so no extra 0.5 factor.
        self.assertAlmostEqual(totals["household_kwh"], 5.5)
        self.assertAlmostEqual(totals["solar_kwh"], 1.0)
        self.assertEqual(totals["reading_count"], 2)

    def test_day_selection_excludes_other_days(self):
        selected = self.data.get_day_readings("2020-01-02")

        self.assertEqual(len(selected), 1)
        self.assertAlmostEqual(
            selected["household_energy_kwh"].iloc[0], 3.0
        )

    def test_readings_are_sorted_by_time(self):
        self.data.set_readings(self.readings.iloc[::-1])
        stored = self.data.get_readings()

        self.assertTrue(stored["date"].is_monotonic_increasing)
        self.assertEqual(
            stored["household_energy_kwh"].tolist(),
            [3.75, 1.75, 3.0],
        )

    def test_setup_loads_a_csv_file(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "readings.csv"
            self.readings.to_csv(source, index=False)

            loaded = DashboardData(source)
            loaded.setup()

            totals = loaded.get_daily_totals("2020-01-01")
            self.assertAlmostEqual(totals["household_kwh"], 5.5)
            self.assertEqual(len(loaded.get_readings()), 3)

    def test_outside_changes_do_not_change_stored_readings(self):
        self.readings.loc[0, "base_load_kwh"] = 999.0

        returned = self.data.get_readings()
        returned.loc[0, "base_load_kwh"] = 500.0

        stored = self.data.get_readings()
        self.assertEqual(stored.loc[0, "base_load_kwh"], 1.0)
        self.assertEqual(stored.loc[0, "household_energy_kwh"], 3.75)

    def test_rejects_input_that_is_not_a_dataframe(self):
        with self.assertRaises(DashboardError):
            self.data.set_readings([1, 2, 3])

    def test_rejects_empty_readings(self):
        with self.assertRaises(DashboardError):
            self.data.set_readings(pd.DataFrame())

    def test_reports_a_missing_load_column(self):
        bad = self.readings.drop(columns=["hvac_load_kwh"])

        with self.assertRaisesRegex(DashboardError, "hvac_load_kwh"):
            self.data.set_readings(bad)

    def test_rejects_negative_energy(self):
        bad = self.readings.copy()
        bad.loc[0, "pv_energy_kwh"] = -1.0

        with self.assertRaises(DashboardError):
            self.data.set_readings(bad)

    def test_rejects_energy_that_is_not_a_number(self):
        bad = self.readings.copy()
        bad["base_load_kwh"] = ["broken", 0.5, 2.0]

        with self.assertRaises(DashboardError):
            self.data.set_readings(bad)

    def test_rejects_missing_and_infinite_energy(self):
        for value in [float("nan"), float("inf")]:
            with self.subTest(value=value):
                bad = self.readings.copy()
                bad.loc[0, "base_load_kwh"] = value

                with self.assertRaises(DashboardError):
                    self.data.set_readings(bad)

    def test_rejects_invalid_timestamps(self):
        bad = self.readings.copy()
        bad.loc[0, "date"] = "not a date"

        with self.assertRaises(DashboardError):
            self.data.set_readings(bad)

    def test_rejects_duplicate_timestamps(self):
        bad = self.readings.copy()
        bad.loc[1, "date"] = bad.loc[0, "date"]

        with self.assertRaises(DashboardError):
            self.data.set_readings(bad)

    def test_reports_a_day_without_readings(self):
        with self.assertRaises(DashboardError):
            self.data.get_day_readings("2030-01-01")

    def test_chart_prepares_household_and_solar_series(self):
        chart = EnergyChart()
        selected = self.data.get_day_readings("2020-01-01")

        prepared = chart.prepare_data(selected)

        self.assertEqual(
            list(prepared.columns),
            ["Time", "Household consumption", "Solar generation"],
        )
        self.assertEqual(
            prepared["Household consumption"].tolist(),
            [3.75, 1.75],
        )
        self.assertEqual(prepared["Solar generation"].tolist(), [0.4, 0.6])

    def test_chart_rejects_invalid_settings(self):
        with self.assertRaises(DashboardError):
            EnergyChart(title=" ")

        with self.assertRaises(DashboardError):
            EnergyChart(show_components="yes")

    def test_csv_export_contains_only_the_selected_day(self):
        dashboard = EnergyDashboard(self.data, EnergyChart())
        dashboard.set_selected_day("2020-01-02")

        exported = dashboard.export_selected_day()
        restored = pd.read_csv(StringIO(exported.decode("utf-8")))

        self.assertEqual(len(restored), 1)
        self.assertAlmostEqual(
            restored["household_energy_kwh"].iloc[0], 3.0
        )
        self.assertAlmostEqual(restored["pv_energy_kwh"].iloc[0], 1.5)

    def test_dashboard_rejects_data_that_has_not_been_loaded(self):
        with self.assertRaises(DashboardError):
            EnergyDashboard(DashboardData(), EnergyChart())


if __name__ == "__main__":
    unittest.main()
