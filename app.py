from pathlib import Path

import streamlit as st

from dashboard import DashboardData, EnergyChart, EnergyDashboard


def main():
    st.set_page_config(page_title="Group 21 | Energy Dashboard", layout="wide")
    source = Path(__file__).parent / "data" / "Full_HA_dataset.csv"
    try:
        data = DashboardData(source)
        data.setup()
        chart = EnergyChart()
        dashboard = EnergyDashboard(data, chart)
        dashboard.render()
    except (OSError, ValueError) as error:
        st.error(f"The dashboard could not load the readings: {error}")
        st.info("Check the dataset file and its columns, then reload the page.")


if __name__ == "__main__":
    main()
