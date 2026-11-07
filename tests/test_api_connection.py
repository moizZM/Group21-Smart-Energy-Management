import json
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

import pandas as pd

import api_server
import app as dashboard_app


def sample_readings():
    return pd.DataFrame({
        "date": ["01/01/2020 00:00", "01/01/2020 00:30"],
        "base_load_kwh": [1.0, 0.5],
        "hvac_load_kwh": [2.0, 1.0],
        "washing_machine_kwh": [0.5, 0.0],
        "dishwasher_kwh": [0.25, 0.25],
        "pv_energy_kwh": [0.4, 0.6],
    })


class FlaskConnectionTests(unittest.TestCase):

    def setUp(self):
        self.client = api_server.app.test_client()

    def test_api_returns_checked_readings(self):
        with patch(
            "api_server.load_dashboard_readings",
            return_value=sample_readings(),
        ):
            response = self.client.get("/api/readings")

        result = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["reading_count"], 2)
        self.assertEqual(
            result["readings"][0]["date"], "01/01/2020 00:00"
        )
        self.assertAlmostEqual(
            result["readings"][0]["household_energy_kwh"], 3.75
        )

    def test_api_reports_a_missing_database(self):
        with patch(
            "api_server.load_dashboard_readings",
            side_effect=FileNotFoundError("Database not found"),
        ):
            response = self.client.get("/api/readings")

        self.assertEqual(response.status_code, 500)
        self.assertIn("Database not found", response.get_json()["error"])

    def test_api_reports_a_database_failure(self):
        with patch(
            "api_server.load_dashboard_readings",
            side_effect=api_server.DatabaseError("Test database failure"),
        ):
            response = self.client.get("/api/readings")

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Test database failure", response.get_json()["error"]
        )

    def test_api_rejects_missing_energy_columns(self):
        readings = sample_readings().drop(columns=["pv_energy_kwh"])

        with patch(
            "api_server.load_dashboard_readings",
            return_value=readings,
        ):
            response = self.client.get("/api/readings")

        self.assertEqual(response.status_code, 500)
        self.assertIn("pv_energy_kwh", response.get_json()["error"])

    def test_api_rejects_negative_energy(self):
        readings = sample_readings()
        readings.loc[0, "base_load_kwh"] = -1.0

        with patch(
            "api_server.load_dashboard_readings",
            return_value=readings,
        ):
            response = self.client.get("/api/readings")

        self.assertEqual(response.status_code, 500)
        self.assertIn("negative", response.get_json()["error"])


class DashboardConnectionTests(unittest.TestCase):

    def test_client_reads_a_valid_response(self):
        payload = {
            "reading_count": 2,
            "readings": sample_readings().to_dict(orient="records"),
        }
        response = BytesIO(json.dumps(payload).encode("utf-8"))

        with patch("app.urlopen", return_value=response):
            readings = dashboard_app.fetch_readings()

        self.assertIsInstance(readings, pd.DataFrame)
        self.assertEqual(len(readings), 2)
        self.assertEqual(readings.loc[0, "base_load_kwh"], 1.0)

    def test_client_rejects_broken_json(self):
        response = BytesIO(b"{broken json")

        with patch("app.urlopen", return_value=response):
            with self.assertRaises(ValueError):
                dashboard_app.fetch_readings()

    def test_client_rejects_a_response_without_readings(self):
        response = BytesIO(b'{"reading_count": 2}')

        with patch("app.urlopen", return_value=response):
            with self.assertRaises(ValueError):
                dashboard_app.fetch_readings()

    def test_client_rejects_readings_that_are_not_a_list(self):
        response = BytesIO(b'{"readings": "wrong format"}')

        with patch("app.urlopen", return_value=response):
            with self.assertRaises(ValueError):
                dashboard_app.fetch_readings()

    def test_client_reports_an_unavailable_server(self):
        with patch(
            "app.urlopen",
            side_effect=URLError("Server unavailable"),
        ):
            with self.assertRaises(URLError):
                dashboard_app.fetch_readings()

    def test_dashboard_shows_an_error_when_connection_fails(self):
        with patch(
            "app.fetch_readings",
            side_effect=URLError("Server unavailable"),
        ), patch("app.st") as screen, patch(
            "app.EnergyDashboard"
        ) as dashboard:
            dashboard_app.main()

        screen.error.assert_called_once()
        screen.info.assert_called_once()
        dashboard.assert_not_called()

    def test_dashboard_shows_an_error_for_invalid_response_data(self):
        with patch(
            "app.fetch_readings",
            side_effect=ValueError("Invalid response data"),
        ), patch("app.st") as screen, patch(
            "app.EnergyDashboard"
        ) as dashboard:
            dashboard_app.main()

        screen.error.assert_called_once()
        screen.info.assert_called_once()
        dashboard.assert_not_called()


if __name__ == "__main__":
    unittest.main()