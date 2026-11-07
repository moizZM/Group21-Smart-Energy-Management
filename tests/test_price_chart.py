import unittest

import pandas as pd

from dashboard import EnergyChart


class PriceChartTests(unittest.TestCase):

    def setUp(self):
        self.chart = EnergyChart()
        self.readings = pd.DataFrame({
            "date": pd.to_datetime([
                "2020-01-01 00:00",
                "2020-01-01 00:30",
            ]),
            "rtp_usd_per_kwh": [0.025, 0.030],
        })

    def test_prepares_time_and_price_columns(self):
        prepared = self.chart.prepare_price_data(self.readings)

        self.assertEqual(list(prepared.columns), ["Time", "Price"])
        self.assertEqual(prepared["Price"].tolist(), [0.025, 0.030])
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(prepared["Time"])
        )

    def test_converts_numeric_price_strings(self):
        readings = self.readings.copy()
        readings["rtp_usd_per_kwh"] = ["0.025", "0.030"]

        prepared = self.chart.prepare_price_data(readings)

        self.assertEqual(prepared["Price"].tolist(), [0.025, 0.030])

    def test_accepts_negative_prices(self):
        readings = self.readings.copy()
        readings["rtp_usd_per_kwh"] = [-0.01, 0.030]

        prepared = self.chart.prepare_price_data(readings)

        self.assertEqual(prepared["Price"].tolist(), [-0.01, 0.030])

    def test_rejects_a_missing_price_column(self):
        readings = self.readings.drop(columns=["rtp_usd_per_kwh"])

        with self.assertRaises(ValueError):
            self.chart.prepare_price_data(readings)

    def test_rejects_empty_readings(self):
        readings = self.readings.iloc[:0]

        with self.assertRaises(ValueError):
            self.chart.prepare_price_data(readings)

    def test_rejects_invalid_prices(self):
        for value in ["broken", None, float("nan"), float("inf")]:
            with self.subTest(value=value):
                readings = self.readings.copy()
                readings["rtp_usd_per_kwh"] = [value, 0.030]

                with self.assertRaises(ValueError):
                    self.chart.prepare_price_data(readings)

    def test_rejects_text_timestamps(self):
        readings = self.readings.copy()
        readings["date"] = readings["date"].dt.strftime(
            "%m/%d/%Y %H:%M"
        )

        with self.assertRaises(ValueError):
            self.chart.prepare_price_data(readings)

    def test_does_not_change_original_readings(self):
        original = self.readings.copy(deep=True)

        prepared = self.chart.prepare_price_data(self.readings)
        prepared.loc[0, "Price"] = 999.0

        pd.testing.assert_frame_equal(self.readings, original)


if __name__ == "__main__":
    unittest.main()