from math import isfinite

import pandas as pd
import streamlit as st


class EnergyChart:

    def __init__(
        self,
        title="Household consumption and solar generation",
        show_components=False,
    ):
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
            raise ValueError("The chart title cannot be blank.")
        self._title = title.strip()

    def get_show_components(self):
        return self._show_components

    def set_show_components(self, show_components):
        if not isinstance(show_components, bool):
            raise ValueError("The chart option must be True or False.")
        self._show_components = show_components

    def prepare_data(self, readings):
        columns = ["date", "household_energy_kwh", "pv_energy_kwh"]

        if readings.empty or not set(columns).issubset(readings.columns):
            raise ValueError(
                "The chart needs prepared household and solar readings."
            )

        chart_data = readings[columns].copy()

        if not pd.api.types.is_datetime64_any_dtype(chart_data["date"]):
            raise ValueError("Chart timestamps must be datetime values.")

        return chart_data.rename(columns={
            "date": "Time",
            "household_energy_kwh": "Household consumption",
            "pv_energy_kwh": "Solar generation",
        })

    def prepare_price_data(self, readings):
        columns = ["date", "rtp_usd_per_kwh"]

        if readings.empty or not set(columns).issubset(readings.columns):
            raise ValueError("Electricity price readings are missing.")

        price_data = readings[columns].copy()

        if not pd.api.types.is_datetime64_any_dtype(price_data["date"]):
            raise ValueError("Price timestamps must be datetime values.")

        prices = pd.to_numeric(
            price_data["rtp_usd_per_kwh"], errors="coerce"
        )

        if prices.isna().any() or not prices.map(isfinite).all():
            raise ValueError("Electricity prices contain invalid values.")

        # Negative electricity prices are allowed.
        price_data["rtp_usd_per_kwh"] = prices

        return price_data.rename(columns={
            "date": "Time",
            "rtp_usd_per_kwh": "Price",
        })

    def render(self, readings):
        chart_data = self.prepare_data(readings)

        st.subheader(self._title)
        st.line_chart(
            chart_data,
            x="Time",
            y=["Household consumption", "Solar generation"],
            x_label="Time",
            y_label="Energy per 30 minutes (kWh)",
            color=["#2563eb", "#e5a000"],
            height=350,
            width="stretch",
        )
        st.caption(
            "Move over the graph to inspect readings. "
            "Drag inside it to zoom."
        )

        if "rtp_usd_per_kwh" in readings.columns:
            price_data = self.prepare_price_data(readings)

            st.subheader("Electricity price")
            st.line_chart(
                price_data,
                x="Time",
                y="Price",
                x_label="Time",
                y_label="Price (USD/kWh)",
                color="#16a34a",
                height=250,
                width="stretch",
            )

        if self._show_components:
            names = {
                "date": "Time",
                "base_load_kwh": "Base load",
                "hvac_load_kwh": "Heating / cooling",
                "washing_machine_kwh": "Washing machine",
                "dishwasher_kwh": "Dishwasher",
            }

            st.subheader("Household consumption by appliance")
            st.line_chart(
                readings[list(names)].rename(columns=names),
                x="Time",
                y=list(names.values())[1:],
                x_label="Time",
                y_label="Energy per 30 minutes (kWh)",
                height=280,
                width="stretch",
            )