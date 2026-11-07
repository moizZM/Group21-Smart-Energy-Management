import pandas as pd
import streamlit as st
from .errors import DashboardError


class EnergyChart:

    def __init__(self, title="Household consumption and solar generation", show_components=False):
        self._title = ""
        self._show_components = False
        self.setup(title, show_components)

    def setup(self, title, show_components=False):
        self.set_title(title)
        self.set_show_components(show_components)

    def get_title(self):
        return self._title

    def set_title(self, title):
        if not isinstance(title, str) or not title.strip():
            raise DashboardError("The chart title cannot be blank.")
        self._title = title.strip()

    def get_show_components(self):
        return self._show_components

    def set_show_components(self, show_components):
        if not isinstance(show_components, bool):
            raise DashboardError("The chart option must be True or False.")
        self._show_components = show_components

    def prepare_data(self, readings):
        columns = ["date", "household_energy_kwh", "pv_energy_kwh"]
        if readings.empty or not set(columns).issubset(readings.columns):
            raise DashboardError("The chart needs prepared household and solar readings.")
        chart_data = readings[columns].copy()
        if not pd.api.types.is_datetime64_any_dtype(chart_data["date"]):
            raise DashboardError("Chart timestamps must be datetime values.")
        return chart_data.rename(columns={
            "date": "Time", "household_energy_kwh": "Household consumption",
            "pv_energy_kwh": "Solar generation",
        })

    def render(self, readings):
        chart_data = self.prepare_data(readings)
        st.subheader(self._title)
        st.line_chart(
            chart_data, x="Time", y=["Household consumption", "Solar generation"],
            x_label="Time", y_label="Energy per 30 minutes (kWh)",
            color=["#2563eb", "#e5a000"], height=350, width="stretch",
        )
        st.caption("Move over the graph to inspect readings. Drag inside it to zoom.")

        if self._show_components:
            names = {
                "date": "Time", "base_load_kwh": "Base load", "hvac_load_kwh": "Heating / cooling",
                "washing_machine_kwh": "Washing machine", "dishwasher_kwh": "Dishwasher",
            }
            st.subheader("Household consumption by appliance")
            st.line_chart(
                readings[list(names)].rename(columns=names), x="Time",
                y=list(names.values())[1:], x_label="Time",
                y_label="Energy per 30 minutes (kWh)", height=280, width="stretch",
            )
