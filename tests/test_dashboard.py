from datetime import date
from io import StringIO
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from dashboard import DashboardData, EnergyChart, EnergyDashboard


def example_readings():
    return pd.DataFrame({
        "date": ["1/2/2020 0:00", "1/1/2020 0:30", "1/1/2020 0:00"],
        "base_load_kwh": [1.0, 0.5, 0.5],
        "hvac_load_kwh": [2.0, 0.2, 0.3],
        "washing_machine_kwh": [0.0, 0.1, 0.0],
        "dishwasher_kwh": [0.0, 0.0, 0.2],
        "pv_energy_kwh": [0.4, 0.1, 0.0],
    })


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.data = DashboardData()
        self.data.set_readings(example_readings())
        self.chart = EnergyChart()
        self.dashboard = EnergyDashboard(self.data, self.chart)

    def test_date_filter_returns_only_selected_day(self):
        result = self.data.get_day_readings(date(2020, 1, 1))
        self.assertEqual(len(result), 2)
        self.assertTrue((result["date"].dt.date == date(2020, 1, 1)).all())
        self.assertTrue(result["date"].is_monotonic_increasing)

    def test_totals_include_all_four_loads_without_extra_time_factor(self):
        totals = self.data.get_daily_totals(date(2020, 1, 1))
        self.assertAlmostEqual(totals["household_kwh"], 1.8)
        self.assertAlmostEqual(totals["solar_kwh"], 0.1)
        self.assertEqual(totals["reading_count"], 2)

    def test_getter_and_setter_do_not_share_mutable_data(self):
        original = example_readings()
        self.data.set_readings(original)
        original.loc[0, "base_load_kwh"] = 999
        returned = self.data.get_readings()
        returned.loc[0, "base_load_kwh"] = 777
        self.assertEqual(self.data.get_daily_totals(date(2020, 1, 2))["household_kwh"], 3.0)

    def test_invalid_energy_does_not_replace_valid_readings(self):
        for value in ["broken", None, float("inf"), -1.0]:
            with self.subTest(value=value):
                bad = example_readings().astype({"pv_energy_kwh": "object"})
                bad.loc[0, "pv_energy_kwh"] = value
                with self.assertRaises(ValueError):
                    self.data.set_readings(bad)
                self.assertEqual(len(self.data.get_readings()), 3)

    def test_empty_or_missing_columns_are_rejected(self):
        for bad in [pd.DataFrame(), example_readings().drop(columns="hvac_load_kwh")]:
            with self.assertRaises(ValueError):
                self.data.set_readings(bad)

    def test_invalid_and_duplicate_dates_are_rejected(self):
        for value in ["not a date", None, "1/1/2020 0:30"]:
            bad = example_readings()
            bad.loc[0, "date"] = value
            with self.assertRaises(ValueError):
                self.data.set_readings(bad)

    def test_preparsed_dates_from_team_are_accepted(self):
        readings = example_readings()
        readings["date"] = pd.to_datetime(readings["date"], format="%m/%d/%Y %H:%M")
        self.data.set_readings(readings)
        self.assertEqual(len(self.data.get_available_days()), 2)

    def test_leap_day_readings_are_supported(self):
        readings = example_readings().iloc[:1].copy()
        readings.loc[0, "date"] = "2/29/2020 0:00"
        self.data.set_readings(readings)
        self.assertEqual(self.data.get_available_days(), [date(2020, 2, 29)])
        self.assertEqual(self.data.get_daily_totals(date(2020, 2, 29))["reading_count"], 1)

    def test_csv_setup_uses_source_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "readings.csv"
            example_readings().to_csv(path, index=False)
            data = DashboardData(path)
            data.setup()
            self.assertEqual(data.get_source_path(), path)
            self.assertEqual(len(data.get_readings()), 3)

    def test_missing_source_and_missing_file_report_errors(self):
        with self.assertRaises(ValueError):
            DashboardData().setup()
        with self.assertRaises(FileNotFoundError):
            DashboardData("does_not_exist.csv").setup()

    def test_unknown_day_is_rejected(self):
        with self.assertRaises(ValueError):
            self.dashboard.set_selected_day(date(2030, 1, 1))
        self.assertEqual(self.dashboard.get_selected_day(), date(2020, 1, 1))

    def test_export_matches_selected_day(self):
        self.dashboard.set_selected_day(date(2020, 1, 2))
        exported = pd.read_csv(StringIO(self.dashboard.export_selected_day().decode("utf-8")))
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported["date"][0], "2020-01-02")
        self.assertEqual(exported["household_energy_kwh"][0], 3.0)

    def test_chart_preserves_dates_and_energy_values(self):
        readings = self.data.get_day_readings(date(2020, 1, 1))
        chart_data = self.chart.prepare_data(readings)
        self.assertEqual(chart_data.columns.tolist(), ["Time", "Household consumption", "Solar generation"])
        self.assertAlmostEqual(chart_data["Household consumption"].sum(), 1.8)
        self.assertEqual(readings.columns.tolist(), self.data.get_readings().columns.tolist())

    def test_configuration_getters_and_setters(self):
        self.chart.set_title("Energy readings")
        self.chart.set_show_components(True)
        self.dashboard.set_title("My dashboard")
        self.assertEqual(self.chart.get_title(), "Energy readings")
        self.assertTrue(self.chart.get_show_components())
        self.assertEqual(self.dashboard.get_title(), "My dashboard")
        with self.assertRaises(ValueError):
            self.chart.set_show_components("yes")
        with self.assertRaises(ValueError):
            self.dashboard.set_title(" ")

    def test_unloaded_data_cannot_create_dashboard(self):
        with self.assertRaises(ValueError):
            EnergyDashboard(DashboardData(), self.chart)

    def test_dashboard_collaborators_can_be_replaced(self):
        new_data = DashboardData()
        new_data.set_readings(example_readings().iloc[:1])
        new_chart = EnergyChart("Replacement chart")
        self.dashboard.set_data(new_data)
        self.dashboard.set_chart(new_chart)
        self.assertIs(self.dashboard.get_data(), new_data)
        self.assertIs(self.dashboard.get_chart(), new_chart)
        self.assertEqual(self.dashboard.get_selected_day(), date(2020, 1, 2))
        with self.assertRaises(ValueError):
            self.dashboard.set_data(DashboardData())
        with self.assertRaises(ValueError):
            self.dashboard.set_chart(None)
        self.assertIs(self.dashboard.get_data(), new_data)
        self.assertIs(self.dashboard.get_chart(), new_chart)

    def test_real_dataset_totals_match_independent_sum(self):
        path = Path(__file__).parents[1] / "data" / "Full_HA_dataset.csv"
        raw = pd.read_csv(path)
        raw["date"] = pd.to_datetime(raw["date"], format="%m/%d/%Y %H:%M")
        data = DashboardData(path)
        data.setup()
        days = data.get_available_days()
        for day in [days[0], days[len(days) // 2], days[-1]]:
            with self.subTest(day=day):
                rows = raw[raw["date"].dt.date == day]
                expected = float(rows[["base_load_kwh", "hvac_load_kwh", "washing_machine_kwh", "dishwasher_kwh"]].sum().sum())
                self.assertAlmostEqual(data.get_daily_totals(day)["household_kwh"], expected)


if __name__ == "__main__":
    unittest.main()
