import json
from urllib.request import urlopen

import pandas as pd
import streamlit as st

from dashboard import DashboardData, EnergyChart, EnergyDashboard


def fetch_readings():
    url = "http://127.0.0.1:5000/api/readings"

    with urlopen(url, timeout=30) as response:
        result = json.load(response)

    if not isinstance(result, dict) or not isinstance(
        result.get("readings"), list
    ):
        raise ValueError("The API returned an unexpected data format.")

    return pd.DataFrame(result["readings"])


def main():
    st.set_page_config(
        page_title="Group 21 | Energy Dashboard",
        layout="wide",
    )

    try:
        readings = fetch_readings()

        data = DashboardData()
        data.set_readings(readings)

        chart = EnergyChart()
        dashboard = EnergyDashboard(data, chart)
        dashboard.render()

    except (OSError, ValueError) as error:
        st.error(f"The dashboard could not load the readings: {error}")
        st.info(
            "Make sure the Flask server is running in the other terminal, "
            "then reload the page."
        )


if __name__ == "__main__":
    main()