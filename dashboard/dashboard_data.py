from math import isfinite
from pathlib import Path

import pandas as pd


class DashboardData:

    LOAD_COLUMNS = [
        "base_load_kwh", "hvac_load_kwh",
        "washing_machine_kwh", "dishwasher_kwh",
    ]
    ENERGY_COLUMNS = LOAD_COLUMNS + ["pv_energy_kwh"]

    def __init__(self, source_path=None):
        self._source_path = None
        self._readings = pd.DataFrame()
        self.set_source_path(source_path)

    def setup(self):
        if self._source_path is None:
            raise ValueError("Choose a dataset path before calling setup().")
        self.set_readings(pd.read_csv(self._source_path))

    def get_source_path(self):
        return self._source_path

    def set_source_path(self, source_path):
        if source_path is not None and not str(source_path).strip():
            raise ValueError("The dataset path cannot be blank.")
        self._source_path = Path(source_path) if source_path is not None else None

    def get_readings(self):
        # Return a copy to protect the stored readings.
        return self._readings.copy(deep=True)

    def set_readings(self, readings):
        if not isinstance(readings, pd.DataFrame):
            raise ValueError("Readings must be a pandas DataFrame.")
        if readings.empty:
            raise ValueError("The dataset has no readings.")

        required = ["date"] + self.ENERGY_COLUMNS
        missing = [column for column in required if column not in readings.columns]
        if missing:
            raise ValueError("Missing columns: " + ", ".join(missing))

        prepared = readings.copy(deep=True)
        if pd.api.types.is_datetime64_any_dtype(prepared["date"]):
            dates = prepared["date"]
        else:
            dates = pd.to_datetime(
                prepared["date"], format="%m/%d/%Y %H:%M", errors="coerce"
            )
        if dates.isna().any():
            raise ValueError("Some dates are missing or invalid. Expected month/day/year hour:minute.")
        if dates.duplicated().any():
            raise ValueError("Each reading must have a unique timestamp.")
        prepared["date"] = dates

        for column in self.ENERGY_COLUMNS:
            values = pd.to_numeric(prepared[column], errors="coerce")
            if values.isna().any() or not values.map(isfinite).all():
                raise ValueError(f"Column {column} contains missing or invalid energy values.")
            if (values < 0).any():
                raise ValueError(f"Column {column} contains negative energy values.")
            prepared[column] = values

        # The readings are already in kWh.
        prepared["household_energy_kwh"] = prepared[self.LOAD_COLUMNS].sum(axis=1)
        self._readings = prepared.sort_values("date").reset_index(drop=True)

    def get_available_days(self):
        if self._readings.empty:
            return []
        return sorted(self._readings["date"].dt.date.unique().tolist())

    def get_day_readings(self, selected_day):
        if self._readings.empty:
            raise ValueError("Load the readings first.")
        day = pd.Timestamp(selected_day).date()
        result = self._readings[self._readings["date"].dt.date == day]
        if result.empty:
            raise ValueError(f"No readings are available for {day}.")
        return result.copy(deep=True)

    def get_daily_totals(self, selected_day):
        readings = self.get_day_readings(selected_day)
        return {
            "household_kwh": float(readings["household_energy_kwh"].sum()),
            "solar_kwh": float(readings["pv_energy_kwh"].sum()),
            "reading_count": len(readings),
        }
