"""Validation and cleaning of reading data (Pandas): `DataCleaner` and `QualityReport`."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

NUMERIC = ["energy_kwh", "price", "occupancy", "temperature", "indoor_temperature",
           "hvac_status", "solar_kwh"]
# Short gaps in slowly changing values may be bridged; energy, solar and status never are.
FILL_COLUMNS = ["price", "temperature", "indoor_temperature"]


def check_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    """Raise ValueError if a required column is missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")


def _counter(name: str, doc: str) -> property:
    """Build a property (getter and validating setter) for one counter of the report."""
    def getter(self: "QualityReport") -> int:
        return self._counts[name]

    def setter(self: "QualityReport", value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
        self._counts[name] = value

    return property(getter, setter, doc=doc)


class QualityReport:
    """Data-quality summary of one import: what was found, dropped and stored."""

    COUNTERS = ("rows_in", "bad_timestamps", "missing_energy", "duplicates",
                "invalid_readings", "values_interpolated", "rows_saved", "rows_stored_new")

    rows_in = _counter("rows_in", "Rows received.")
    bad_timestamps = _counter("bad_timestamps", "Rows whose time could not be read.")
    missing_energy = _counter("missing_energy", "Rows without an energy value.")
    duplicates = _counter("duplicates", "Repeated (meter, time) rows removed.")
    invalid_readings = _counter("invalid_readings", "Rows outside the allowed limits.")
    values_interpolated = _counter("values_interpolated", "Short gaps that were filled.")
    rows_saved = _counter("rows_saved", "Rows that passed all checks.")
    rows_stored_new = _counter("rows_stored_new", "Rows that were new in the database.")

    def __init__(self, layout: str = "", **counts: int) -> None:
        self._counts: dict[str, int] = dict.fromkeys(self.COUNTERS, 0)
        self._layout = ""
        self.layout = layout
        for name, value in counts.items():
            if name not in self.COUNTERS:
                raise ValueError(f"Unknown report field: {name}")
            setattr(self, name, value)

    @property
    def layout(self) -> str:
        """'wide' or 'long' (the layout of the input file), empty if unknown."""
        return self._layout

    @layout.setter
    def layout(self, value: str) -> None:
        if value not in ("", "wide", "long"):
            raise ValueError("layout must be 'wide', 'long' or empty")
        self._layout = value

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"layout": self._layout} if self._layout else {}
        result.update(self._counts)
        return result

    def __repr__(self) -> str:
        return f"QualityReport({self.as_dict()})"


class DataCleaner:
    """Removes bad rows: missing or unreadable values, duplicates, out-of-range readings."""

    def __init__(self, limits: dict[str, Any] | None = None, max_gap_fill: int = 2) -> None:
        self._limits = self._check_limits(limits or {})
        self._max_gap_fill = self._check_gap(max_gap_fill)
        self._last_report = QualityReport()

    # ---- initialisation helpers (validation) ---------------------------------
    @staticmethod
    def _check_limit(column: str, low: float, high: float) -> tuple[float, float]:
        if not isinstance(column, str) or not column:
            raise ValueError("limit column must be a non-empty string")
        if low > high:
            raise ValueError(f"lower limit of '{column}' must not exceed the upper limit")
        return float(low), float(high)

    @classmethod
    def _check_limits(cls, limits: dict[str, Any]) -> dict[str, tuple[float, float]]:
        checked = {}
        for column, bounds in limits.items():
            if len(bounds) != 2:
                raise ValueError(f"limit of '{column}' needs [low, high]")
            checked[column] = cls._check_limit(column, bounds[0], bounds[1])
        return checked

    @staticmethod
    def _check_gap(value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("max_gap_fill must be a non-negative integer")
        return value

    # ---- getters and setters -------------------------------------------------
    @property
    def limits(self) -> dict[str, tuple[float, float]]:
        return dict(self._limits)

    @limits.setter
    def limits(self, value: dict[str, Any]) -> None:
        self._limits = self._check_limits(value)

    @property
    def max_gap_fill(self) -> int:
        """Longest run of missing price/temperature values that may be interpolated."""
        return self._max_gap_fill

    @max_gap_fill.setter
    def max_gap_fill(self, value: int) -> None:
        self._max_gap_fill = self._check_gap(value)

    @property
    def last_report(self) -> QualityReport:
        return self._last_report

    # ---- configuration -------------------------------------------------------
    def set_limit(self, column: str, low: float, high: float) -> None:
        self._limits[column] = self._check_limit(column, low, high)

    def remove_limit(self, column: str) -> None:
        self._limits.pop(column, None)

    # ---- the cleaning itself -------------------------------------------------
    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, QualityReport]:
        """Clean a readings DataFrame and return (clean_df, data-quality report)."""
        report = QualityReport(rows_in=len(df))
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        for col in NUMERIC:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        report.bad_timestamps = int(df["timestamp"].isna().sum())
        report.missing_energy = int(df["energy_kwh"].isna().sum())
        df = df.dropna(subset=["timestamp", "energy_kwh"])

        report.duplicates = int(df.duplicated(["asset_id", "timestamp"]).sum())
        df = df.drop_duplicates(["asset_id", "timestamp"])

        invalid = pd.Series(False, index=df.index)
        for col, (low, high) in self._limits.items():
            if col in df.columns:
                invalid |= df[col].notna() & ((df[col] < low) | (df[col] > high))
        report.invalid_readings = int(invalid.sum())
        df = df[~invalid].copy()

        filled = 0
        if self._max_gap_fill > 0:
            for col in FILL_COLUMNS:
                if col in df.columns:
                    before = int(df[col].isna().sum())
                    df[col] = df.groupby("asset_id")[col].transform(
                        lambda s: s.interpolate(limit=self._max_gap_fill, limit_direction="both"))
                    filled += before - int(df[col].isna().sum())
        report.values_interpolated = filled

        df = df.sort_values(["asset_id", "timestamp"])
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        report.rows_saved = len(df)
        self._last_report = report
        logger.info("Cleaning finished: %s", report)
        return df, report


def clean_readings(df: pd.DataFrame,
                   limits: dict[str, list[float]]) -> tuple[pd.DataFrame, dict[str, int]]:
    """Convenience wrapper around `DataCleaner` that returns the report as a dict."""
    cleaned, report = DataCleaner(limits).clean(df)
    return cleaned, report.as_dict()
