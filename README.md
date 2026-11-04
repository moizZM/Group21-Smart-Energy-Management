# AI-Powered Smart Energy Management System
## Group 21

A Python project that simulates household electricity use,
solar generation, battery storage and smart appliances.

The system aims to reduce electricity costs and carbon
emissions while maintaining household comfort.

## Team Members

| Member | Responsibility |
|---|---|
| Varikuti Pravallika | Assets and Database |
| Elizabeth Chikhladze | Deterministic Logic Engine: energy, cost and carbon calculations |
| Joachim Kennedy Gomes | AI Engine and Summary |
| Moiz Zaheer Malik | Web UI / Dashboard |

<img width="1090" height="1226" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/a1140a31-b350-4657-a1fe-550c15872238" />



## Planned Features

- Load energy, solar, price and occupancy data.
- Model batteries and smart appliances using Python classes.
- Recommend battery charging, discharging and appliance schedules.
- Calculate costs, savings, carbon emissions and sustainability scores.
- Display results, recommendations and alerts on a dashboard.

## Dataset

Residential HEMS dataset by Mozhgan Rahmatinia, Version 1.
Data contains readings at 30-minute intervals.

Source: https://data.mendeley.com/datasets/23s96gn2j7/1
License: CC BY 4.0

## System Design

The rendered diagram below shows Moiz's implemented dashboard classes.
Each class has a constructor, setup logic, and getter/setter methods.

![Dashboard UML class diagram](docs/dashboard_classes.svg)

## Team Presentation

**Presentation link: pending the team's recording.**

For Homework 1, record one combined team video lasting 3 to 5 minutes. Each
member explains their own implemented classes. 

## Project Status

The dashboard reads the included CSV. Flask, SQLite, the logic engine, and the AI
engine are later integration work they are not claimed as implemented here.
The visible daily energy totals describe the original readings, not optimised savings.

## Moiz's Homework 1 Contribution

| Class | Responsibility | Example getter and setter |
|---|---|---|
| `DashboardData` | Load and validate readings, filter by day, prepare display totals | `get_readings()` / `set_readings()` |
| `EnergyChart` | Prepare and display interactive household and solar charts | `get_title()` / `set_title()` |
| `EnergyDashboard` | Coordinate the objects, date selection, metrics, table, and CSV export | `get_selected_day()` / `set_selected_day()` |

`EnergyDashboard` uses aggregation: it receives a `DashboardData` object and an
`EnergyChart` object. These objects can be used independently. Each class has its
own `__init__()` and `setup()` methods. Internal attributes use the underscore
convention, and setters validate changes. Getters return copies of stored readings.

The dashboard keeps the original day selection and readings table, replaces the
static plot with interactive charts, and adds appliance breakdown and CSV download.

### How to run

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Files and next integration

- `app.py`: creates the objects and starts the dashboard.
- `dashboard/`: the three dashboard classes and package exports.
- `docs/dashboard_classes.svg`: rendered UML diagram.
- `docs/dashboard_classes.mmd`: editable diagram source.

The existing dataset has 47,040 readings across 980 available days. Each energy
value is kWh per 30-minute interval. Household energy includes base load, HVAC,
washing machine, and dishwasher; interval kWh values are summed without an extra
0.5 factor. The price column is in USD/kWh and is preserved without currency conversion.

For integration, another subsystem can pass a DataFrame into
`DashboardData.set_readings()`. This allows Pravallika's data access code to
supply readings later without rewriting the charts.

### Team submission checklist

- Integrate at least three unique classes from each member (at least 12 total).
- Keep the shared project runnable and review each other's code.
- Add all subsystem diagrams and their connections.
- Record and link the combined team video, with every member explaining their part.
- Submit the correct `Homeworkassignment001` branch link through the course assignment.
