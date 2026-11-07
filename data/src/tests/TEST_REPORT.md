# Assets and Database Unit Test Report

## Test run

- Runner: Python standard-library `unittest`
- Command (from the `data` directory):
  `..\.venv\Scripts\python.exe -m unittest discover -s src/tests -v`
- Result: **18 tests passed, 0 failures, 0 errors**
- Statement/line coverage: **78%** (719 of 922 statements executed)
- Coverage scope: `src.assets` and `src.data_base` production modules
- Database: temporary SQLite database created by the tests; the project database
  and household dataset are not modified.

## Test cases

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_battery_charge_and_discharge_respect_capacity` | Battery charging efficiency, state of charge, and discharge behavior. |
| 2 | `test_battery_rejects_negative_charge` | Invalid negative charging raises `AssetError`. |
| 3 | `test_battery_capacity_cannot_be_less_than_stored_energy` | Capacity cannot be reduced below stored energy. |
| 4 | `test_asset_configuration_rolls_back_after_invalid_setting` | A failed multi-property update leaves the asset unchanged. |
| 5 | `test_solar_panel_calculates_and_tracks_generation` | Solar generation calculation and last-generation state. |
| 6 | `test_appliance_consumes_energy_only_when_on` | Appliance energy use depends on its on/off state. |
| 7 | `test_building_balances_generation_demand_and_battery` | Building balances solar output, appliance demand, battery, and grid. |
| 8 | `test_building_rejects_duplicate_asset_ids` | A building rejects duplicate asset identifiers. |
| 9 | `test_asset_round_trips_through_sqlite` | An asset can be saved and reconstructed from SQLite. |
| 10 | `test_loading_unknown_asset_raises_database_error` | Loading a missing asset raises `DatabaseError`. |
| 11 | `test_readings_insert_once_and_can_be_retrieved` | Readings insert once and duplicate timestamps are ignored. |
| 12 | `test_readings_filter_by_asset_and_time_range` | Readings can be filtered by asset and date range. |
| 13 | `test_simulation_results_and_alerts_round_trip` | Results and alerts persist, and alerts can be acknowledged. |
| 14 | `test_importer_cleans_and_saves_wide_csv` | Wide CSV data is reshaped, cleaned, stored, and not duplicated on re-import. |
| 15 | `test_importer_reports_missing_input_file` | A missing input file raises `DataImportError`. |
| 16 | `test_importer_reports_unsupported_file_type` | An unsupported input extension raises `DataImportError`. |
| 17 | `test_importer_reports_missing_required_column` | Missing required input fields raise `DataValidationError`. |
| 18 | `test_cleaner_drops_invalid_timestamps_and_duplicate_rows` | Invalid timestamps and duplicate readings are removed and counted. |

Re-run the command above whenever the subsystem or its tests change so the
reported result reflects the latest code.
