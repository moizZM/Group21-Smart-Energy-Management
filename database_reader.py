import sys
from pathlib import Path

# Pravallika's src folder is inside data.
PROJECT_FOLDER = Path(__file__).resolve().parent
DATA_FOLDER = PROJECT_FOLDER / "data"
SOURCE_FOLDER = DATA_FOLDER / "src"

sys.path.insert(0, str(DATA_FOLDER))

from src.data_base.data_import import load_config
from src.data_base.database_manager import DatabaseManager


def load_dashboard_readings():
    config = load_config(str(SOURCE_FOLDER / "config.json"))
    database_path = SOURCE_FOLDER / config["db_path"]

    if not database_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    with DatabaseManager(str(database_path)) as database:
        readings = database.get_readings()

    if readings.empty:
        raise ValueError("The database has no readings.")

    # Select the four loads, excluding the calculated household total.
    meters = config["wide_format"]["meters"]
    load_rows = readings[readings["asset_id"].isin(meters)]

    # Put each load into its own column.
    energy = load_rows.pivot(
        index="timestamp",
        columns="asset_id",
        values="energy_kwh",
    )

    energy = energy.rename(columns=meters)
    energy = energy.reindex(columns=list(meters.values()))

    # Solar and price are repeated for each meter.
    # Take them only once, from the household total rows.
    total_rows = readings[
        readings["asset_id"] == config["total_asset_id"]
    ]

    context = total_rows.set_index("timestamp")[
        ["solar_kwh", "price"]
    ].rename(columns={
        "solar_kwh": "pv_energy_kwh",
        "price": "rtp_usd_per_kwh",
    })

    result = energy.join(context, how="outer")
    result = result.rename_axis("date").reset_index()
    result.columns.name = None

    return result.sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    from dashboard.dashboard_data import DashboardData

    dashboard_data = DashboardData()
    dashboard_data.set_readings(load_dashboard_readings())

    prepared = dashboard_data.get_readings()

    print(prepared.head().to_string(index=False))
    print("\nTimestamps:", len(prepared))
    print(
        "Household energy:",
        round(prepared["household_energy_kwh"].sum(), 2),
        "kWh",
    )
    print(
        "Solar generation:",
        round(prepared["pv_energy_kwh"].sum(), 2),
        "kWh",
    )