Residential HEMS Dataset Based on Home Assistant Simulation and Online Exogenous Data
======================================================================================

Dataset overview
----------------
This dataset provides a simulation-based residential home energy management system
(HEMS) data environment for research on HVAC control, thermal comfort, shiftable
appliance scheduling, photovoltaic (PV) generation, real-time electricity pricing,
battery-aware energy management, and residential demand response.

The household-related variables were generated using Home Assistant automation rules
designed to represent a four-person household. These simulated variables include
occupancy count, appliance requests, appliance energy profiles, desired indoor
temperature, active comfort indicator, non-controllable base load, HVAC operating
state, and HVAC load.

The Home Assistant-based variables were then combined with online exogenous data,
including CAISO real-time electricity prices, NSRDB-based PV generation, and outdoor
temperature for a Los Angeles / SP-15 California region. All variables were
synchronized to a common 30-minute time resolution.

This dataset is not an optimized controller or an intelligent HEMS by itself. It is a
reusable data environment intended for researchers to implement, train, test, and
compare their own control, optimization, and machine-learning methods for residential
HEMS applications.

Dataset files
-------------
The released dataset includes the following files:

- Full_HA_dataset.csv
  Complete 30-minute residential HEMS dataset containing all records. This file
  includes a split column that identifies whether each row belongs to train, eval,
  test_real, or test_comprehensive.

- HA_train.csv
  Training split for model development and training.

- HA_eval.csv
  Evaluation split for validation, model selection, or checkpoint selection.

- HA_test_real.csv
  Real-test split for evaluating performance under conditions closer to the observed
  data distribution.

- HA_test_comprehensive.csv
  Comprehensive-test split for evaluating generalization under more diverse operating
  conditions.

- HA_Data_Dictionary.xlsx
  Excel workbook documenting dataset variables, units, data types, source categories,
  online data sources, and processing notes. It contains the following sheets:
  data dictionary, read me, source categories, and online_source.

- Source Description.pdf
  Detailed documentation of the Home Assistant-based household scenario, dataset
  construction process, online data sources, appliance and HVAC assumptions,
  occupancy patterns, preprocessing steps, and synchronization of simulated and
  online variables.

- LICENSE.txt
  Dataset license information.

Main dataset characteristics
----------------------------
- Household type: one simulated four-person residential household
- Time period: 2020-01-01 00:00:00 to 2022-09-07 23:30:00
- Time resolution: 30 minutes
- Time steps per day: 48
- Total number of records: 47,040
- Number of days: 980
- Data splits: train, eval, test_real, test_comprehensive

Main variables
--------------
The dataset contains the following columns:

- date
  Timestamp of each 30-minute record.

- split
  Data split assignment. This column is included only in the full combined dataset.

- base_load_kwh
  Non-controllable household base electricity consumption per 30-minute interval.

- rtp_usd_per_kwh
  Real-time electricity price in USD/kWh. The raw CAISO price was converted from
  USD/MWh to USD/kWh.

- washing_machine_kwh
  Washing machine energy consumption per 30-minute interval.

- dishwasher_kwh
  Dishwasher energy consumption per 30-minute interval.

- washing_machine_request
  Binary indicator of a washing machine request.

- dishwasher_request
  Binary indicator of a dishwasher request.

- pv_energy_kwh
  PV generation available during each 30-minute interval.

- away_return_steps
  Number of 30-minute steps remaining until the first occupant returns home.

- occupancy_count
  Number of occupants at home.

- comfort_active
  Binary indicator showing whether thermal comfort is active and relevant.

- outdoor_temperature_c
  Outdoor air temperature in degrees Celsius.

- indoor_temperature_c
  Simulated indoor air temperature in degrees Celsius.

- desired_temperature_c
  Desired indoor temperature setpoint in degrees Celsius.

- hvac_state
  HVAC operating mode represented by an integer code:
  0 = OFF, 1 = HEAT_LOW, 2 = HEAT_HIGH, 3 = COOL_LOW, 4 = COOL_HIGH.

- hvac_load_kwh
  HVAC consumption level associated with hvac_state.

Online data sources
-------------------
The online exogenous variables were prepared from the following sources:

- Real-time electricity price:
  EnergyOnline CAISO Real-time Price, TH_SP15 / SP-15 California region.
  The raw price was provided in USD/MWh and converted to USD/kWh by dividing by 1000.

- PV generation and outdoor temperature:
  National Solar Radiation Database (NSRDB), NREL/OEDI, selected for a Los Angeles-area
  location to maintain geographic consistency with the SP-15 electricity price region.

Detailed source information, URLs, access dates, units, and processing notes are
provided in HA_Data_Dictionary.xlsx and Source Description.pdf.

Intended use
------------
This dataset can be used for research and benchmarking in areas such as:

- residential home energy management systems;
- HVAC control and thermal comfort management;
- active-only comfort evaluation;
- shiftable appliance scheduling;
- demand response under real-time electricity pricing;
- PV-aware residential energy management;
- battery scheduling and energy optimization;
- reinforcement learning, constrained optimization, and model predictive control for HEMS.

Reproducibility notes
---------------------
The full dataset includes the split column to support reproducible experiments.
The separate split files are provided for convenience and do not include the split
column because each file already corresponds to a single predefined split.

Users should consult HA_Data_Dictionary.xlsx and Source Description.pdf before using
the dataset, especially for units, variable meanings, data sources, and processing
assumptions.

Privacy statement
-----------------
The household activity data were generated from a simulated Home Assistant scenario
and do not contain real personal or private household data. The dataset is intended
for public research use.

License
-------
This dataset is released under the Creative Commons Attribution 4.0 International
License (CC BY 4.0). See LICENSE.txt for details.

Citation
--------
If you use this dataset, please cite the dataset DOI assigned by Mendeley Data.

Suggested citation format:

[Author(s)]. Residential HEMS Dataset Based on Home Assistant Simulation and Online
Exogenous Data. Mendeley Data, Version 1. DOI: [add DOI after publication].
