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


def show_daily_metrics(day):
    st.subheader("Daily cost and carbon")
    url = f"http://127.0.0.1:5000/api/metrics/{day.isoformat()}"

    try:
        with urlopen(url, timeout=30) as response:
            metrics = json.load(response)

        cost = float(metrics["total_cost_usd"])
        carbon = float(metrics["total_carbon_kg"])
    except (OSError, ValueError, KeyError, TypeError):
        st.warning("Could not load the cost and carbon estimates for this day.")
        return

    cost_column, carbon_column = st.columns(2)
    cost_column.metric("Estimated electricity cost", f"${cost:.2f}")
    carbon_column.metric("Estimated carbon emissions", f"{carbon:.2f} kg CO₂")

    action = metrics.get("battery_action")
    action_time = metrics.get("battery_action_time")
    if action and action_time:
        st.subheader("Battery recommendation")
        st.write(f"**{action}** at **{action_time}** (highest price interval)")

    summary = metrics.get("sustainability_summary")
    if summary:
        st.subheader("Sustainability summary")
        st.write(summary)

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
        show_daily_metrics(dashboard.get_selected_day())

    except (OSError, ValueError) as error:
        st.error(f"The dashboard could not load the readings: {error}")
        st.info(
            "Make sure the Flask server is running in the other terminal, "
            "then reload the page."
        )


if __name__ == "__main__":
    main()