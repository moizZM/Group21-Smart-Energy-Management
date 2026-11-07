import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from data.src.data_base.database_manager import DatabaseManager


# ==========================================
# Configuration & Setup
# ==========================================
class ConfigManager:
    DEFAULT_CONFIG = {
        "active_threshold_kwh": 0.01,
        "peak_threshold_kw": 50.0,
        "carbon_intensity_peak": 0.450,
        "carbon_intensity_offpeak": 0.300,
        "peak_start_hour": 14,
        "peak_end_hour": 19,
        "baseline_energy_kwh": 500.0
    }

    def __init__(self):
        self._filepath = ""
        self._config = self.DEFAULT_CONFIG.copy()
        
    def initialize_config(self, filepath: str = None):
        if filepath is None:
            base_dir = Path(__file__).parent.parent
            self._filepath = str(base_dir / "config" / "config.json")
        else:
            self._filepath = filepath

        try:
            with open(self._filepath, 'r') as f:
                loaded_config = json.load(f)
                self._config.update(loaded_config)
        except FileNotFoundError:
            print(f"Warning: {filepath} not found. Using default configuration.")

    def get_filepath(self) -> str: return self._filepath
    def set_filepath(self, filepath: str): self._filepath = filepath

    def get_config(self) -> dict: return self._config
    def set_config(self, config: dict): self._config = config


class CleanDatabaseIterator:
    def __init__(self):
        self._records = []
        self._current_index = 0
        self._total_rows = 0

    def initialize_iterator(self, energy_db: DatabaseManager):
        """Fetches clean data using DatabaseManager class."""
        df = energy_db.get_readings() 
        self._records = df.to_dict(orient='records')
        self._current_index = 0
        self._total_rows = len(self._records)

    def get_current_index(self) -> int: return self._current_index
    def set_current_index(self, val: int): self._current_index = val

    def __iter__(self):
        return self

    def __next__(self) -> dict:
        if self._current_index < self._total_rows:
            row = self._records[self._current_index]
            self._current_index += 1
            return row
        raise StopIteration


class AbstractLogicProcessor(ABC):
    def __init__(self):
        self._config_mgr = None

    def initialize_processor(self, config_mgr: ConfigManager):
        self._config_mgr = config_mgr

    def get_config_mgr(self) -> ConfigManager: return self._config_mgr
    def set_config_mgr(self, mgr: ConfigManager): self._config_mgr = mgr

    def get_config(self) -> dict: 
        return self._config_mgr.get_config()

    @abstractmethod
    def process(self, data: Any) -> Any:
        pass

    def __or__(self, other):
        pipeline = CompositePipeline()
        pipeline.initialize_pipeline(self, other)
        return pipeline


class CompositePipeline(AbstractLogicProcessor):
    def __init__(self):
        super().__init__()
        self._left = None
        self._right = None

    def initialize_pipeline(self, left: AbstractLogicProcessor, right: AbstractLogicProcessor):
        self._left = left
        self._right = right

    def get_left(self): return self._left
    def set_left(self, left): self._left = left
    def get_right(self): return self._right
    def set_right(self, right): self._right = right

    def process(self, data: Any) -> Any:
        intermediate_data = self._left.process(data)
        return self._right.process(intermediate_data)


class ThresholdFilterProcessor(AbstractLogicProcessor):
    def __init__(self):
        super().__init__()

    def process(self, db_iterator: CleanDatabaseIterator) -> list[dict]:
        cfg = self.get_config()
        threshold = cfg["active_threshold_kwh"]
        
        valid_records = []
        for record in db_iterator:
            if record.get('energy_kwh', 0) >= threshold:
                valid_records.append(record)
                
        return valid_records


class ComprehensiveMetricsProcessor(AbstractLogicProcessor):
    def __init__(self):
        super().__init__()

    def process(self, valid_records: list[dict]) -> dict[str, Any]:
        if not valid_records:
            return {}

        cfg = self.get_config()
        df = pd.DataFrame(valid_records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        for col in ['energy_kwh', 'price', 'solar_kwh']:
            if col in df.columns:
                df[col] = df[col].fillna(0.0)

        df['cost'] = df['energy_kwh'] * df['price']

        peak_mask = (df['timestamp'].dt.hour >= cfg["peak_start_hour"]) & \
                    (df['timestamp'].dt.hour <= cfg["peak_end_hour"])
                    
        df['carbon_factor'] = np.where(peak_mask, cfg["carbon_intensity_peak"], cfg["carbon_intensity_offpeak"])
        df['carbon_kg'] = df['energy_kwh'] * df['carbon_factor']

        timestep_df = df.groupby('timestamp').agg(
            total_energy=('energy_kwh', 'sum'),
            total_solar=('solar_kwh', 'max')
        ).reset_index()

        peak_spikes = timestep_df[timestep_df['total_energy'] > cfg["peak_threshold_kw"]]
        peak_records = [{"time": str(row['timestamp']), "val": row['total_energy']} for _, row in peak_spikes.iterrows()]

        timestep_df['self_consumed_kwh'] = np.minimum(timestep_df['total_energy'], timestep_df['total_solar'])
        total_solar_used = timestep_df['self_consumed_kwh'].sum()

        category_breakdown = df.groupby('asset_id')['energy_kwh'].sum().to_dict()
        category_breakdown = {str(k): np.round(v, 4) for k, v in category_breakdown.items()}

        # Totals
        total_energy = df['energy_kwh'].sum()
        total_carbon = df['carbon_kg'].sum()
        total_cost = df['cost'].sum()

        # Sustainability Score (0-100)
        efficiency = min(cfg["baseline_energy_kwh"] / (total_energy + 1e-9), 1.0)
        sus_score = efficiency * 100

        return {
            "run_timestamp": datetime.now().isoformat(timespec="seconds"),
            "total_energy_kwh": np.round(total_energy, 4),
            "total_cost_usd": np.round(total_cost, 4),
            "total_carbon_kg": np.round(total_carbon, 4),
            "sustainability_score": np.round(sus_score, 4),
            "renewable_self_consumption_kwh": np.round(total_solar_used, 4),
            "peak_demands_detected": peak_records,
            "category_breakdown_kwh": category_breakdown
        }


# ==========================================
# Dedicated Output Database Manager
# ==========================================
class OutputDatabaseManager:
    """Creates and manages your subsystem's exclusive SQLite database."""
    def __init__(self):
        self._db_path = ""
        self._conn = None

    def initialize_manager(self, db_path: str = "metrics_output.db"):
        self._db_path = db_path
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._create_tables()

    def _create_tables(self):
        with self._conn:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS run_summaries (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp TEXT,
                    total_energy_kwh REAL,
                    total_cost_usd REAL,
                    total_carbon_kg REAL,
                    sustainability_score REAL,
                    renewable_self_consumption_kwh REAL
                );
                CREATE TABLE IF NOT EXISTS category_breakdowns (
                    breakdown_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    asset_category TEXT,
                    energy_kwh REAL,
                    FOREIGN KEY(run_id) REFERENCES run_summaries(run_id)
                );
                CREATE TABLE IF NOT EXISTS peak_demands (
                    peak_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    peak_timestamp TEXT,
                    peak_value_kw REAL,
                    FOREIGN KEY(run_id) REFERENCES run_summaries(run_id)
                );
            """)

    def get_db_path(self) -> str: return self._db_path
    def set_db_path(self, path: str): self._db_path = path

    def save_to_database(self, metrics: dict) -> int:
        """Stores the calculated dictionary relationally into SQLite."""
        with self._conn:
            # Save Summary
            cursor = self._conn.execute(
                """INSERT INTO run_summaries (run_timestamp, total_energy_kwh, total_cost_usd, 
                   total_carbon_kg, sustainability_score, renewable_self_consumption_kwh) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (metrics["run_timestamp"], metrics["total_energy_kwh"], metrics["total_cost_usd"],
                 metrics["total_carbon_kg"], metrics["sustainability_score"], metrics["renewable_self_consumption_kwh"])
            )
            run_id = cursor.lastrowid

            # Save Category Breakdown
            for category, energy in metrics["category_breakdown_kwh"].items():
                self._conn.execute(
                    "INSERT INTO category_breakdowns (run_id, asset_category, energy_kwh) VALUES (?, ?, ?)",
                    (run_id, category, energy)
                )

            # Save Peak Demands
            for peak in metrics["peak_demands_detected"]:
                self._conn.execute(
                    "INSERT INTO peak_demands (run_id, peak_timestamp, peak_value_kw) VALUES (?, ?, ?)",
                    (run_id, peak["time"], peak["val"])
                )
                
        return run_id


# ==========================================
# Controller
# ==========================================
class LogicEngineController:
    """Facade Pattern: Provides a unified interface to the logic subsystem."""
    
    def __init__(self):
        self._config_mgr = ConfigManager()
        self._output_mgr = OutputDatabaseManager()

    def execute_pipeline(self, energy_db_path: str = "energy.db") -> dict:
        try:
            energy_db = DatabaseManager(energy_db_path)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return {}

        base_dir = Path(__file__).parent.parent
        config_file_path = base_dir / "config" / "config.json"
        
        self._config_mgr.initialize_config(str(config_file_path))

        db_iterator = CleanDatabaseIterator()
        db_iterator.initialize_iterator(energy_db)
        
        energy_db.close()

        filter_stage = ThresholdFilterProcessor()
        filter_stage.initialize_processor(self._config_mgr)

        math_stage = ComprehensiveMetricsProcessor()
        math_stage.initialize_processor(self._config_mgr)

        business_logic_pipeline = filter_stage | math_stage

        final_metrics = business_logic_pipeline.process(db_iterator)

        self._output_mgr.initialize_manager("metrics_output.db")
        
        if final_metrics:
            run_id = self._output_mgr.save_to_database(final_metrics)
            print(f"Calculations completed and stored successfully in run_id: {run_id}")
        else:
            print("No valid data found to process.")

        return final_metrics

if __name__ == "__main__":
    # Instantiate the formal controller class
    subsystem_controller = LogicEngineController()
    
    # Execute the subsystem
    test_result = subsystem_controller.execute_pipeline()
    
    # Print the resulting dictionary
    print("\n--- FINAL CALCULATED METRICS ---")
    print(json.dumps(test_result, indent=4))
