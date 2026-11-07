# Hometask 4: Error Handling and Unit Testing

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
