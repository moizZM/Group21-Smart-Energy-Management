import pandas as pd                    # what is this and why we have it here where is it helping us in the code.
import streamlit as st                 # what is this and why we have it here where is it helping us in the code.
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.set_page_config(page_title="Energy Dashboard", layout="wide")   # explain this. and all the lines after this.

st.title("Smart Energy Dashboard")
st.write("Group 21")

# Load the household energy data
data = pd.read_csv("data/Full_HA_dataset.csv")
data["date"] = pd.to_datetime(data["date"], format="%m/%d/%Y %H:%M")

number_of_readings = len(data)
st.write("Dataset loaded:", number_of_readings, "readings")

available_days = sorted(data["date"].dt.date.unique())

selected_day = st.selectbox("Choose a day", available_days)

day_data = data[data["date"].dt.date == selected_day]
# Household consumption includes all four load components
household_energy = (
    day_data["base_load_kwh"]
    + day_data["hvac_load_kwh"]
    + day_data["washing_machine_kwh"]
    + day_data["dishwasher_kwh"]
)

total_consumption = household_energy.sum()
total_solar = day_data["pv_energy_kwh"].sum()

column1, column2 = st.columns(2)

column1.metric("Daily household energy", f"{total_consumption:.2f} kWh")
column2.metric("Daily solar generation", f"{total_solar:.2f} kWh")

st.subheader("Household consumption and solar generation")

fig, ax = plt.subplots(figsize=(10, 4))

ax.plot(day_data["date"], household_energy, label="Household consumption")
ax.plot(day_data["date"], day_data["pv_energy_kwh"], label="Solar generation")

ax.set_xlabel("Time")
ax.set_ylabel("Energy per 30 minutes (kWh)")
ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.margins(x=0)
ax.set_ylim(bottom=0)
ax.legend()
ax.grid(alpha=0.3)

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.write("Readings for this day:", len(day_data))

st.subheader("Selected day's readings")
st.dataframe(day_data)