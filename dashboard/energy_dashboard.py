"""Connect the data, controls and charts. Author: Moiz Zaheer Malik."""

import pandas as pd
import streamlit as st

from .dashboard_data import DashboardData
from .energy_chart import EnergyChart


class EnergyDashboard:
    """Coordinate the dashboard using the two other subsystem classes."""

    def __init__(self, data, chart, title="Smart Energy Dashboard"):
        self._data = None
        self._chart = None
        self._title = ""
        self._selected_day = None
        self.set_data(data)
        self.set_chart(chart)
        self.set_title(title)
        self.setup()

    def setup(self):
        days = self._data.get_available_days()
        if not days:
            raise ValueError("Load the readings before creating the dashboard.")
        self.set_selected_day(days[0])

    def get_data(self):
        return self._data

    def set_data(self, data):
        if not isinstance(data, DashboardData) or not data.get_available_days():
            raise ValueError("The dashboard needs a DashboardData object with loaded readings.")
        self._data = data
        days = data.get_available_days()
        if self._selected_day not in days:
            self._selected_day = days[0]

    def get_chart(self):
        return self._chart

    def set_chart(self, chart):
        if not isinstance(chart, EnergyChart):
            raise ValueError("The dashboard needs an EnergyChart object.")
        self._chart = chart

    def get_title(self):
        return self._title

    def set_title(self, title):
        if not isinstance(title, str) or not title.strip():
            raise ValueError("The dashboard title cannot be blank.")
        self._title = title.strip()

    def get_selected_day(self):
        return self._selected_day

    def set_selected_day(self, selected_day):
        day = pd.Timestamp(selected_day).date()
        if day not in self._data.get_available_days():
            raise ValueError(f"No readings are available for {day}.")
        self._selected_day = day

    def export_selected_day(self):
        readings = self._data.get_day_readings(self._selected_day)
        return readings.to_csv(index=False).encode("utf-8")

    def render(self):
        st.title(self._title)
        st.caption("Group 21 · AI-Powered Smart Energy Management System")
        days = self._data.get_available_days()
        total_rows = len(self._data.get_readings())
        st.write(f"Explore {total_rows:,} readings across {len(days):,} days.")

        selected_day = st.selectbox(
            "Choose a day", days, index=days.index(self._selected_day),
            format_func=lambda day: day.strftime("%d %B %Y"), key="selected_day",
        )
        self.set_selected_day(selected_day)
        self._chart.set_show_components(st.checkbox(
            "Show appliance breakdown", value=self._chart.get_show_components(), key="show_components"
        ))

        readings = self._data.get_day_readings(self._selected_day)
        totals = self._data.get_daily_totals(self._selected_day)
        household, solar, count = st.columns(3)
        household.metric("Daily household energy", f"{totals['household_kwh']:.2f} kWh")
        solar.metric("Daily solar generation", f"{totals['solar_kwh']:.2f} kWh")
        count.metric("Readings for this day", totals["reading_count"])
        self._chart.render(readings)

        st.subheader("Selected day's readings")
        st.download_button(
            "Download this day's readings", data=self.export_selected_day(),
            file_name=f"energy_readings_{self._selected_day}.csv", mime="text/csv",
        )
        st.dataframe(readings, hide_index=True, width="stretch")
        st.caption("Source: Residential HEMS dataset, Mozhgan Rahmatinia, Version 1 · CC BY 4.0")
