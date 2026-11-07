"""File input: `DataImporter` reads CSV or Parquet, reshapes, cleans and stores readings."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .database_manager import DatabaseManager
from .validation import DataCleaner, QualityReport, check_required_columns

logger = logging.getLogger(__name__)

READERS = {".csv": pd.read_csv, ".parquet": pd.read_parquet}


class DataImportError(ValueError):
    """Raised when an input file cannot be read or reshaped for import."""


def load_config(path: str = "config.json") -> dict[str, Any]:
    """Load the JSON configuration file."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load config '{path}': {exc}") from exc


class DataImporter:
    """CSV/Parquet input: read, rename columns, reshape, clean and store the readings."""

    CONFIGURABLE = ("columns", "required_columns", "default_asset_id", "wide_format")

    def __init__(self, config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("config must be a dictionary")
        self._columns = dict(config.get("columns", {}))
        self._required = self._check_required(config.get("required", ["timestamp", "energy_kwh"]))
        self._default_asset_id = self._check_text(config.get("default_asset_id", "meter"))
        self._wide = self._check_wide(config.get("wide_format"))
        self._cleaner = DataCleaner(config.get("limits", {}))
        self._last_report: QualityReport | None = None

    @classmethod
    def from_config_file(cls, path: str = "config.json") -> "DataImporter":
        """Set-up method: build an importer from a JSON configuration file."""
        return cls(load_config(path))

    # ---- initialisation helpers (validation) ---------------------------------
    @staticmethod
    def _check_text(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("default_asset_id must be a non-empty string")
        return value.strip()

    @staticmethod
    def _check_required(columns: list[str]) -> list[str]:
        if not columns or not all(isinstance(c, str) and c for c in columns):
            raise ValueError("required columns must be a non-empty list of names")
        return list(columns)

    @staticmethod
    def _check_wide(wide: dict[str, Any] | None) -> dict[str, Any] | None:
        if wide is not None and not wide.get("meters"):
            raise ValueError("wide_format needs a 'meters' mapping")
        return wide

    # ---- getters and setters -------------------------------------------------
    @property
    def columns(self) -> dict[str, str]:
        """Mapping internal name -> column name in the file."""
        return dict(self._columns)

    @columns.setter
    def columns(self, value: dict[str, str]) -> None:
        self._columns = dict(value)

    @property
    def required_columns(self) -> list[str]:
        return list(self._required)

    @required_columns.setter
    def required_columns(self, value: list[str]) -> None:
        self._required = self._check_required(value)

    @property
    def default_asset_id(self) -> str:
        return self._default_asset_id

    @default_asset_id.setter
    def default_asset_id(self, value: str) -> None:
        self._default_asset_id = self._check_text(value)

    @property
    def wide_format(self) -> dict[str, Any] | None:
        return self._wide

    @wide_format.setter
    def wide_format(self, value: dict[str, Any] | None) -> None:
        self._wide = self._check_wide(value)

    @property
    def cleaner(self) -> DataCleaner:
        return self._cleaner

    @property
    def last_report(self) -> QualityReport | None:
        return self._last_report

    # ---- configuration -------------------------------------------------------
    def configure(self, **settings: Any) -> None:
        """Change several settings at once; unknown names are rejected."""
        unknown = [key for key in settings if key not in self.CONFIGURABLE]
        if unknown:
            raise ValueError(f"Unknown setting(s): {unknown}")
        for key, value in settings.items():
            setattr(self, key, value)

    # ---- reading and reshaping -------------------------------------------------
    @staticmethod
    def read_table(path: str) -> pd.DataFrame:
        """Read a .csv or .parquet file into a DataFrame."""
        file = Path(path)
        if not file.is_file():
            raise DataImportError(f"Input file not found: {path}")
        reader = READERS.get(file.suffix.lower())
        if reader is None:
            raise DataImportError(
                f"Unsupported file type '{file.suffix}'. Use: {', '.join(READERS)}"
            )
        try:
            return reader(file)
        except (OSError, ImportError, pd.errors.ParserError) as exc:
            raise DataImportError(f"Cannot read input file '{path}': {exc}") from exc

    def is_wide_format(self, df: pd.DataFrame) -> bool:
        """True if the table has one column per meter (e.g. the ML dataset layout)."""
        return bool(self._wide) and all(col in df.columns for col in self._wide["meters"].values())

    def reshape_wide(self, df: pd.DataFrame) -> pd.DataFrame:
        """Turn one-row-per-interval data into one row per meter reading.

        `meters` maps asset ids to energy columns; `context` maps reading fields (occupancy,
        price, solar_kwh ...) to source columns repeated on every meter row; `on_if_positive`
        turns codes into 1/0 flags; `derived_total` adds a meter that is the sum of all
        meters (labelled derived).
        """
        wide = self._wide
        if not wide:
            raise DataImportError("No wide_format configured")
        context: dict[str, str] = wide.get("context", {})
        missing = [c for c in ["timestamp", *context.values()] if c not in df.columns]
        if missing:
            raise DataImportError(f"Input data is missing columns: {missing}")

        df = df.copy()
        base = pd.DataFrame({"timestamp": pd.to_datetime(df["timestamp"], errors="coerce")})
        for name, source in context.items():
            base[name] = pd.to_numeric(df[source], errors="coerce")
        if "occupancy" in base:
            base["occupancy"] = base["occupancy"].round()
        for name in wide.get("on_if_positive", []):
            if name in base:
                base[name] = (base[name] > 0).astype(float).where(base[name].notna())

        energy = {meter: pd.to_numeric(df[col], errors="coerce")
                  for meter, col in wide["meters"].items()}
        parts = [base.assign(asset_id=m, energy_kwh=values) for m, values in energy.items()]
        if wide.get("derived_total"):
            total = pd.concat(energy.values(), axis=1).sum(axis=1, skipna=False)
            parts.append(base.assign(asset_id=wide["derived_total"], energy_kwh=total))
        return pd.concat(parts, ignore_index=True)

    # ---- the whole import ------------------------------------------------------
    def import_into(self, path: str, db: DatabaseManager) -> QualityReport:
        """Read a file, clean it and store the readings; return the quality report."""
        df = self.read_table(path)
        df = df.rename(columns={v: k for k, v in self._columns.items() if v in df.columns})
        layout = "wide" if self.is_wide_format(df) else "long"
        if layout == "wide":
            df = self.reshape_wide(df)
        check_required_columns(df, self._required)
        if "asset_id" not in df.columns:
            df["asset_id"] = self._default_asset_id
        clean, report = self._cleaner.clean(df)
        report.layout = layout
        report.rows_stored_new = db.add_readings(clean)
        self._last_report = report
        return report


# ---- convenience functions (thin wrappers around the class) ----------------------
def read_table(path: str) -> pd.DataFrame:
    return DataImporter.read_table(path)


def is_wide_format(df: pd.DataFrame, wide_cfg: dict[str, Any] | None) -> bool:
    return DataImporter({"wide_format": wide_cfg}).is_wide_format(df)


def reshape_wide(df: pd.DataFrame, wide_cfg: dict[str, Any]) -> pd.DataFrame:
    return DataImporter({"wide_format": wide_cfg}).reshape_wide(df)


def import_file(path: str, db: DatabaseManager, cfg: dict[str, Any]) -> dict[str, Any]:
    """Import a CSV or Parquet file into the database; return the quality report as a dict."""
    return DataImporter(cfg).import_into(path, db).as_dict()
