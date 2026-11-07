# Hometask 4: Error Handling and Unit Testing
## Video link explaining Error Handling and Unit Testing of Subsystems:
https://drive.google.com/drive/u/3/folders/18bESrPFPBMTsLYPtu5ILSmlqcQtxHSCx
### Varikuti Pravallika — Assets and Database

My Hometask 4 contribution adds explicit error handling and automated tests for
the assets and database subsystem. The tests cover asset behavior, data
importing and validation, and SQLite storage.

Subsystem files:

- `data/src/assets/`: `EnergyAsset`, `Battery`, `SolarPanel`,
  `SmartAppliance`, `Building`, and the asset factory.
- `data/src/data_base/`: `DatabaseManager`, record classes, CSV/Parquet
  importing, data cleaning, and validation.
- `data/src/tests/test_assets_database.py`: 18 automated unit tests.
- `data/src/tests/TEST_REPORT.md`: test case list and the recorded test and
  statement-coverage results.

The subsystem defines these exception classes:

- `AssetError`: invalid asset settings or operations.
- `DataImportError`: missing, unsupported, or unreadable import files.
- `DataValidationError`: missing required reading columns.
- `DatabaseError`: database connection or query failures.

These are raised as exceptions so calling code or tests can handle expected
failures explicitly.

## Running subsystem tests

This branch contains the assets/database subsystem and its tests. The full
application entry point and dashboard are on the team's project branch.

## Install dependencies

Run these commands from the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you already have the project environment and dependencies installed, skip
the setup commands.

## Run the tests

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s data/src/tests -v
```

The tests use temporary files and SQLite databases; they do not modify an
application database or the household dataset.

The latest recorded test run passed **18 tests**. The report records **78%
statement/line coverage** for the `src.assets` and `src.data_base` modules; see
[`data/src/tests/TEST_REPORT.md`](data/src/tests/TEST_REPORT.md) for the test
list and measurement details.

## GitHub

Repository: https://github.com/moizZM/Group21-Smart-Energy-Management

Submit the `Homeworkassignment0004` branch for Hometask 4.

### Elizabeth Chikhladze - Logic Engine
The Logic Engine subsystem includes 15 automated unit tests designed to validate core business logic, structural integrity, and edge-case resilience.

#### Test Coverage Breakdown
1. **Configuration Management (Tests 1-3)**

*Fallback Reliability*: Ensures the system successfully loads hardcoded default values if config.json is missing or deleted.

*Dynamic Overrides*: Verifies that loaded JSON parameters correctly overwrite internal defaults.

*Encapsulation*: Confirms that the configuration dictionary is properly isolated and returned.

2. **Data Stream Filtering (Tests 4-6)**

*hreshold Execution*: Validates that readings below the active_threshold_kwh are accurately dropped from the processing pipeline.

*Empty Stream Handling*: Ensures the filter safely processes an empty database without crashing.

*Missing Key Resilience*: Confirms KeyError exceptions are prevented if incoming database records are missing expected columns.

3. **Mathematical Logic & Edge Cases (Tests 7-12)**

*Cost & Carbon Precision*: Verifies the Cost = Energy * Price formula and tests the dynamic shift between peak (0.450) and off-peak (0.300) carbon intensities based on timestamps.

*Score Capping*: Ensures the 0-100 sustainability score never exceeds 100%, even with near-zero energy consumption.

*Peak Demand Detection*: Validates that any localized energy spike exceeding the 50.0 kW threshold is successfully detected and logged.

*Null-Value Substitution*: Ensures missing prices or blank solar readings default to 0.0 rather than causing a NaN math failure.

4. **Pipeline Orchestration & Error Recovery (Tests 13-15)**

*Composite Chaining*: Tests the operator overloading (|) to ensure the filter and math processors chain together correctly and share state.

*Safe Fallbacks*: Verifies that the ErrorManager successfully intercepts fatal crashes (e.g., division by zero) and returns a formatted fallback dictionary to prevent dashboard failures.

*Dynamic Grouping*: Ensures energy usage is correctly aggregated by asset_id regardless of how many distinct assets the external database contains.

------
### Unit Test Suite Summary | AI Engine subsystem
### Joachim Kennedy Gomes

| Test Case / Method | Tested Functionality & Assertions |
| :--- | :--- |
| **`test_01_battery_soc`** | Validates initial Battery State of Charge (SoC) calculation (defaults to 50% capacity). |
| **`test_02_battery_charge`** | Tests battery charging mechanics and verifies correct energy accumulation against efficiency boundaries. |
| **`test_03_config_manager`** | Verifies that configuration parameters (active thresholds, tariff rates) load successfully from JSON. |
| **`test_04_ai_engine_init`** | Confirms proper object instantiation and operational status transition from `INITIALIZED` to `RUNNING`. |
| **`test_05_advisor_recommendation`** | Tests rule-based battery dispatch logic (`DISCHARGE`, `CHARGE`, `HOLD`) under various price and solar generation boundaries. |
| **`test_06_summarizer_report`** | Validates OpenAI integration and offline fallback formatting for executive sustainability reports. |
| **`test_07_database_init`** | Asserts correct SQLite schema creation and table initialization (`cleaned_data`, `ai_logs`). |
------

---

### Moiz Zaheer Malik — Dashboard

My Hometask 4 contribution adds the dashboard classes, a custom exception
class and 18 automated unit tests.

- `dashboard/errors.py`: defines `DashboardError`, which inherits from
  `ValueError`.
- `dashboard/dashboard_data.py`: validates readings and prepares daily totals.
- `dashboard/energy_chart.py`: prepares chart data and validates chart settings.
- `dashboard/energy_dashboard.py`: manages day selection and CSV export.
- `tests/test_dashboard.py`: contains the dashboard tests.

The tests cover daily totals, day filtering, timestamp sorting, CSV loading
and export, chart preparation, protection against outside data changes,
and rejection of invalid readings or settings.

Run the dashboard tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The dashboard test run passed 18 tests. These tests use sample readings and
temporary files. They do not require a running Flask server or an application
database.
