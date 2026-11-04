"""SQLite storage: assets, readings, simulation results and alerts."""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.assets.energy_asset import EnergyAsset
from src.assets.factory import asset_from_record

from .records import Alert, EnergyReading, SimulationResult

logger = logging.getLogger(__name__)

READING_COLUMNS = ["asset_id", "timestamp", "energy_kwh", "price", "occupancy", "temperature",
                   "indoor_temperature", "hvac_status", "solar_kwh"]


class DatabaseError(RuntimeError):
    """Raised when a database operation fails."""


class DatabaseManager:
    """Stores and retrieves assets, readings, simulation results and alerts."""

    def __init__(self, db_path: str = "energy.db") -> None:
        self._db_path = ""
        self._connect(db_path)

    def _connect(self, db_path: str) -> None:
        """Set-up method: open the database and make sure the tables exist."""
        try:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            self._conn = conn
            self._migrate_legacy_tables()
            self._create_tables()
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseError(f"Cannot open database '{db_path}': {exc}") from exc
        self._db_path = str(db_path)

    @property
    def db_path(self) -> str:
        return self._db_path

    @db_path.setter
    def db_path(self, new_path: str) -> None:
        """Switch to another database file (the old connection is closed)."""
        old = self._conn
        self._connect(new_path)
        old.close()

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def _run(self, sql: str, params: Any = (), many: bool = False) -> sqlite3.Cursor:
        try:
            with self._conn:  # commits on success, rolls back on error
                if many:
                    return self._conn.executemany(sql, params)
                return self._conn.execute(sql, params)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database error: {exc}") from exc

    def _migrate_legacy_tables(self) -> None:
        """Replace the empty first-draft tables (old schema) with the current schema."""
        columns = {row[1] for row in self._conn.execute("PRAGMA table_info(assets)")}
        if not columns or "specs" in columns:
            return
        rows = 0
        for table in ("assets", "energy_readings"):
            try:
                rows += self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.OperationalError:
                pass
        if rows:
            raise DatabaseError("Old-format assets/energy_readings tables contain data; "
                                "migrate them manually before using this version")
        self._conn.execute("DROP TABLE IF EXISTS energy_readings")
        self._conn.execute("DROP TABLE IF EXISTS assets")
        self._conn.commit()
        logger.info("Replaced empty legacy tables with the current schema")

    def _create_tables(self) -> None:
        for sql in (
            """CREATE TABLE IF NOT EXISTS assets(
                asset_id TEXT PRIMARY KEY, asset_type TEXT NOT NULL, name TEXT,
                specs TEXT NOT NULL, state TEXT NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS energy_readings(
                asset_id TEXT, timestamp TEXT NOT NULL, energy_kwh REAL NOT NULL,
                price REAL, occupancy INTEGER, temperature REAL,
                indoor_temperature REAL, hvac_status INTEGER, solar_kwh REAL,
                UNIQUE(asset_id, timestamp))""",
            """CREATE TABLE IF NOT EXISTS simulation_results(
                run_id INTEGER PRIMARY KEY AUTOINCREMENT, run_name TEXT NOT NULL,
                totals TEXT, cost REAL, parameters TEXT, details TEXT,
                created_at TEXT)""",
            """CREATE TABLE IF NOT EXISTS alerts(
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL REFERENCES assets(asset_id),
                severity TEXT NOT NULL, message TEXT, timestamp TEXT,
                acknowledged INTEGER DEFAULT 0)""",
        ):
            self._conn.execute(sql)
        existing = {row[1] for row in self._conn.execute("PRAGMA table_info(energy_readings)")}
        for name, sql_type in (("indoor_temperature", "REAL"), ("hvac_status", "INTEGER"),
                               ("solar_kwh", "REAL")):
            if name not in existing:   # upgrade a database created by an earlier version
                self._conn.execute(f"ALTER TABLE energy_readings ADD COLUMN {name} {sql_type}")
        self._conn.commit()

    # ---- assets -------------------------------------------------------
    def save_asset(self, asset: EnergyAsset) -> None:
        self._run(
            """INSERT INTO assets(asset_id, asset_type, name, specs, state)
               VALUES(?,?,?,?,?)
               ON CONFLICT(asset_id) DO UPDATE SET asset_type=excluded.asset_type,
               name=excluded.name, specs=excluded.specs, state=excluded.state""",
            (asset.asset_id, asset.asset_type, asset.name,
             json.dumps(asset.specifications()), json.dumps(asset.state())))

    def load_asset(self, asset_id: str) -> EnergyAsset:
        row = self._run("SELECT asset_type, name, specs, state FROM assets WHERE asset_id=?",
                        (asset_id,)).fetchone()
        if row is None:
            raise DatabaseError(f"Asset not found: {asset_id}")
        return asset_from_record(row[0], asset_id, row[1], json.loads(row[2]), json.loads(row[3]))

    def list_assets(self) -> list[EnergyAsset]:
        ids = [r[0] for r in self._run("SELECT asset_id FROM assets ORDER BY asset_id")]
        return [self.load_asset(i) for i in ids]

    # ---- readings -----------------------------------------------------
    def add_reading(self, reading: EnergyReading) -> None:
        self._run(
            f"INSERT OR IGNORE INTO energy_readings({','.join(READING_COLUMNS)}) "
            f"VALUES({','.join('?' * len(READING_COLUMNS))})",
            (reading.asset_id, reading.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
             reading.energy_kwh, reading.price, reading.occupancy, reading.temperature,
             reading.indoor_temperature, reading.hvac_status, reading.solar_kwh))

    def add_readings(self, df: pd.DataFrame) -> int:
        """Bulk insert a cleaned DataFrame; return the number of new rows stored."""
        out = df.reindex(columns=READING_COLUMNS)
        out = out.astype(object).where(out.notna(), None)
        before = self._conn.total_changes
        self._run(
            f"INSERT OR IGNORE INTO energy_readings({','.join(READING_COLUMNS)}) "
            f"VALUES({','.join('?' * len(READING_COLUMNS))})",
            list(out.itertuples(index=False, name=None)), many=True)
        return self._conn.total_changes - before

    def get_readings(self, asset_id: str | None = None, start: str | None = None,
                     end: str | None = None) -> pd.DataFrame:
        """Historical readings as a DataFrame (interface for other subsystems)."""
        sql, params = "SELECT * FROM energy_readings WHERE 1=1", []
        for clause, value in (("AND asset_id=?", asset_id), ("AND timestamp>=?", start),
                              ("AND timestamp<=?", end)):
            if value:
                sql += " " + clause
                params.append(value)
        try:
            df = pd.read_sql(sql + " ORDER BY timestamp", self._conn, params=params)
        except (sqlite3.Error, pd.errors.DatabaseError) as exc:
            raise DatabaseError(f"Cannot read readings: {exc}") from exc
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def reading_sources(self) -> list[str]:
        """Asset ids (meters) that have stored readings."""
        return [r[0] for r in self._run(
            "SELECT DISTINCT asset_id FROM energy_readings ORDER BY asset_id")]

    def summarise_readings(self, asset_id: str | None = None) -> dict[str, float]:
        """Totals, average, peak and cost; cost covers only readings that have a price."""
        sql = ("SELECT COUNT(*), COALESCE(SUM(energy_kwh),0), COALESCE(AVG(energy_kwh),0), "
               "COALESCE(MAX(energy_kwh),0), COALESCE(SUM(energy_kwh*price),0), COUNT(price) "
               "FROM energy_readings")
        params: tuple = ()
        if asset_id:
            sql, params = sql + " WHERE asset_id=?", (asset_id,)
        n, total, mean, peak, cost, priced = self._run(sql, params).fetchone()
        return {"readings": n, "total_kwh": total, "mean_kwh": mean, "peak_kwh": peak,
                "total_cost": cost, "priced_readings": priced}

    # ---- simulation results -------------------------------------------
    def save_result(self, result: SimulationResult) -> int:
        cur = self._run(
            """INSERT INTO simulation_results(run_name, totals, cost, parameters, details,
               created_at) VALUES(?,?,?,?,?,?)""",
            (result.run_name, json.dumps(result.totals), result.cost,
             json.dumps(result.parameters), json.dumps(result.details),
             datetime.now().isoformat(timespec="seconds")))
        return int(cur.lastrowid)

    def get_results(self, run_name: str | None = None) -> list[SimulationResult]:
        sql = "SELECT run_name, totals, cost, parameters, details FROM simulation_results"
        params: tuple = ()
        if run_name:
            sql, params = sql + " WHERE run_name=?", (run_name,)
        return [SimulationResult(r[0], json.loads(r[1]), r[2], json.loads(r[3]), json.loads(r[4]))
                for r in self._run(sql + " ORDER BY run_id", params)]

    # ---- alerts -------------------------------------------------------
    def add_alert(self, alert: Alert) -> int:
        cur = self._run(
            "INSERT INTO alerts(asset_id, severity, message, timestamp, acknowledged) "
            "VALUES(?,?,?,?,?)",
            (alert.asset_id, alert.severity, alert.message,
             alert.timestamp.isoformat(timespec="seconds"), int(alert.acknowledged)))
        return int(cur.lastrowid)

    def get_alerts(self, unacknowledged_only: bool = False) -> list[Alert]:
        sql = "SELECT alert_id, asset_id, severity, message, timestamp, acknowledged FROM alerts"
        if unacknowledged_only:
            sql += " WHERE acknowledged=0"
        return [Alert(r[1], r[2], r[3], datetime.fromisoformat(r[4]), bool(r[5]), r[0])
                for r in self._run(sql + " ORDER BY alert_id")]

    def acknowledge_alert(self, alert_id: int) -> None:
        cur = self._run("UPDATE alerts SET acknowledged=1 WHERE alert_id=?", (alert_id,))
        if cur.rowcount == 0:
            raise DatabaseError(f"Alert not found: {alert_id}")
