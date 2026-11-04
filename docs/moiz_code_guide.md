# Moiz's code guide

This guide explains the dashboard contribution for Homework 1 in simple words.

## Start here

Read `app.py`, then `dashboard_data.py`, `energy_chart.py`, and `energy_dashboard.py`.
The entry file creates three objects and asks the dashboard to display itself.

## What the OOP terms mean in this code

| Term | Example |
|---|---|
| Class | `DashboardData` is the description of a data object. |
| Object | `data = DashboardData(source)` creates one actual data object. |
| Constructor | `__init__()` sets starting values when the object is created. |
| Attribute | `_selected_day` remembers the day selected by the user. |
| Method | `get_day_readings(day)` is a function belonging to an object. |
| Getter | `get_title()` reads the stored title. |
| Setter | `set_title(title)` checks and changes the title. |
| Encapsulation | The object manages its attributes through methods. A leading underscore marks an internal attribute by Python convention; it does not block direct access. |
| Aggregation | `EnergyDashboard` receives and uses separate data and chart objects. Those objects can exist without the dashboard. |

There is no custom inheritance here. The three classes have different jobs, so
making one inherit from another would not describe their relationship correctly.

## Follow one click

1. The user selects a date in the Streamlit select box.
2. `EnergyDashboard.set_selected_day()` checks that the date exists.
3. `DashboardData.get_day_readings()` returns only that day's readings.
4. `get_daily_totals()` adds the household and solar energy for display.
5. `EnergyChart.render()` displays the graph using the filtered rows.
6. `export_selected_day()` produces a CSV containing those same rows.

Streamlit reruns the entry file when a control changes. The select box keeps its
value using the `selected_day` widget key. The chosen value is then passed into
the new dashboard object during that run.

## Energy calculations used for display

Household energy for each reading is the sum of base load, HVAC, washing machine,
and dishwasher energy. Daily energy is the sum of those interval values.
The source columns already contain kWh per 30 minutes, so we do not multiply
them by 0.5 again. These descriptive totals are not Elizabeth's optimisation,
cost, carbon, or baseline comparison engine.

For 1 January 2020 in the included dataset, there are 48 readings.
Household energy is 55.31038403 kWh and solar energy is 9.24288329 kWh.
The interface rounds these to 55.31 and 9.24 kWh.

## Input and output for the team

`DashboardData.set_readings()` accepts a pandas DataFrame with these fields:

| Field | Meaning |
|---|---|
| `date` | A pandas datetime column, or source strings such as `1/1/2020 0:00`. |
| `base_load_kwh` | Base household energy per interval. |
| `hvac_load_kwh` | Heating/cooling energy per interval. |
| `washing_machine_kwh` | Washing machine energy per interval. |
| `dishwasher_kwh` | Dishwasher energy per interval. |
| `pv_energy_kwh` | Solar generation per interval. |

Other columns are preserved in the readings table and download. The supplied
price column is `rtp_usd_per_kwh`, in USD, not EUR. This version does not calculate
cost or convert currencies.

The setter validates the input before replacing the object's data. Invalid
updates leave the previous valid readings unchanged. The getter returns a copy,
so editing that copy does not accidentally change the object's stored readings.

For Homework 3, Pravallika's data access code can supply a DataFrame through
`set_readings()`. A Flask endpoint can return records, which the dashboard can
convert back to a DataFrame. JSON timestamps should be parsed to pandas datetime
before this setter is called. The Flask/MySQL connection is not implemented in
this Homework 1 contribution.

Later, agree with Elizabeth and Kennedy on result fields and timestamps before
adding cost, carbon, battery, savings, and AI advice panels. Do not invent their
outputs or present placeholder numbers as calculated results.

## What the tests check

Run `python -m unittest discover -s tests -v`.
The checks include date selection, independent energy sums, bad input,
encapsulation, CSV output, and the actual Streamlit controls. Real dataset totals
are checked for the first, middle, and last available days. A separate sample
checks leap day support; leap day is not present in the supplied dataset.
