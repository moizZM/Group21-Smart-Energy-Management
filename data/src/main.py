"""Command-line entry point: import a CSV/Parquet file and show the asset dashboard."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.assets.battery import Battery
from src.assets.building import Building
from src.assets.smart_appliance import SmartAppliance
from src.assets.solar_panel import SolarPanel
from src.data_base.data_import import import_file, load_config
from src.data_base.database_manager import DatabaseManager

ROOT = Path(__file__).resolve().parent


def sample_building() -> Building:
    """Sample assets used for the dashboard prototype."""
    building = Building("South wing")
    building.register_asset(Battery("B1", "Battery", capacity_kwh=10, stored_kwh=7.2))
    building.register_asset(SolarPanel("S1", "Solar roof", area_m2=40))
    building.register_asset(SmartAppliance("A1", "Heat pump", rated_power_kw=2.0, status=True))
    return building


def print_dashboard(db: DatabaseManager) -> None:
    print("\nSmart Energy | Assets")
    for asset in db.list_assets():
        if isinstance(asset, Battery):
            text = f"{asset.state_of_charge_percent:.0f}%"
        elif isinstance(asset, SmartAppliance):
            text = "ON" if asset.status else "OFF"
        else:
            text = f"{asset.state()['last_generation_kwh']:.1f} kWh last step"
        print(f"  {asset.asset_id:<4}{asset.name:<12}{text}")
    print(f"  Alerts ({len(db.get_alerts(unacknowledged_only=True))})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assets and Database subsystem")
    parser.add_argument("--file", "--csv", dest="file", help="CSV or Parquet file with energy data")
    parser.add_argument("--config", default=str(ROOT / "config.json"))
    args = parser.parse_args()

    cfg = load_config(args.config)
    logging.basicConfig(level=cfg.get("log_level", "INFO"))
    with DatabaseManager(str(ROOT / cfg["db_path"])) as db:
        if not db.list_assets():
            for asset in sample_building().assets:
                db.save_asset(asset)
        if args.file:
            print("Data quality summary:")
            for key, value in import_file(args.file, db, cfg).items():
                print(f"  {key}: {value}")
            for source in db.reading_sources():
                s = db.summarise_readings(source)
                cost = (f"{s['total_cost']:.2f} {cfg.get('currency', '')}".strip()
                        if s["priced_readings"] else "n/a (no price data)")
                print(f"  {source}: {s['readings']} readings, total {s['total_kwh']:.1f} kWh, "
                      f"peak {s['peak_kwh']:.2f} kWh, cost {cost}")
        print_dashboard(db)


if __name__ == "__main__":
    main()
