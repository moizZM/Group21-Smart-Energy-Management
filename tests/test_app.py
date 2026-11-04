from datetime import date
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from dashboard import DashboardData


class AppTests(unittest.TestCase):
    def test_day_selection_and_appliance_option(self):
        root = Path(__file__).parents[1]
        app = AppTest.from_file(str(root / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.get("vega_lite_chart")), 1)
        self.assertEqual(app.metric[0].value, "55.31 kWh")

        chosen_day = date(2020, 7, 1)
        app.selectbox[0].set_value(chosen_day).run()
        self.assertEqual(len(app.exception), 0)
        data = DashboardData(root / "data" / "Full_HA_dataset.csv")
        data.setup()
        expected = data.get_daily_totals(chosen_day)
        self.assertEqual(app.metric[0].value, f"{expected['household_kwh']:.2f} kWh")
        self.assertTrue((app.dataframe[0].value["date"].dt.date == chosen_day).all())

        app.checkbox[0].check().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Household consumption by appliance", [x.value for x in app.subheader])
        self.assertEqual(len(app.get("vega_lite_chart")), 2)


if __name__ == "__main__":
    unittest.main()
