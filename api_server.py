from flask import Flask, jsonify

from database_reader import load_dashboard_readings
from dashboard.dashboard_data import DashboardData
from src.data_base.database_manager import DatabaseError

from datetime import date
from pathlib import Path

from logic_engine.logic_engine import ComprehensiveMetricsProcessor, ConfigManager

from ai_engine.optimizer import EnergyAdvisor, Summarizer

app = Flask(__name__)


@app.get("/api/readings")
def get_readings():
    try:
        dashboard_data = DashboardData()
        dashboard_data.set_readings(load_dashboard_readings())
        readings = dashboard_data.get_readings()

        readings["date"] = readings["date"].dt.strftime(
            "%m/%d/%Y %H:%M"
        )

        return jsonify({
            "reading_count": len(readings),
            "readings": readings.to_dict(orient="records"),
        })

    except (FileNotFoundError, ValueError, DatabaseError) as error:
        return jsonify({"error": str(error)}), 500


@app.get("/api/metrics/<day_text>")
def get_daily_metrics(day_text):
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        return jsonify({"error": "Use a date in YYYY-MM-DD format."}), 400

    try:
        data = DashboardData()
        data.set_readings(load_dashboard_readings())

        if day not in data.get_available_days():
            return jsonify({"error": f"No readings for {day}."}), 404

        # Give the logic engine one row per meter and time interval.
        # Using only the four loads avoids counting the household total twice.
        day_readings = data.get_day_readings(day)
        readings = day_readings.melt(
            id_vars=["date", "rtp_usd_per_kwh", "pv_energy_kwh"],
            value_vars=DashboardData.LOAD_COLUMNS,
            var_name="asset_id",
            value_name="energy_kwh",
        )
        readings = readings.rename(columns={
            "date": "timestamp",
            "rtp_usd_per_kwh": "price",
            "pv_energy_kwh": "solar_kwh",
        })

        config = ConfigManager()
        config_path = Path(__file__).resolve().parent / "config" / "config.json"
        config.initialize_config(str(config_path))

        processor = ComprehensiveMetricsProcessor()
        processor.initialize_processor(config)
        metrics = processor.process(readings.to_dict(orient="records"))

        prices = day_readings["rtp_usd_per_kwh"]
        peak_reading = day_readings.loc[prices.idxmax()]

        # Compare the peak price with the selected day's upper price range.
        price_threshold = float(prices.quantile(0.75))
        advisor = EnergyAdvisor(1, price_threshold=price_threshold)
        battery_action = advisor.recommend_battery_action(
            current_price=float(peak_reading["rtp_usd_per_kwh"]),
            pv_generation=float(peak_reading["pv_energy_kwh"]),
        )

        summary = Summarizer(2).generate_sustainability_coach_report(metrics)

        return jsonify({
            "date": day.isoformat(),
            "total_energy_kwh": float(metrics["total_energy_kwh"]),
            "total_cost_usd": float(metrics["total_cost_usd"]),
            "total_carbon_kg": float(metrics["total_carbon_kg"]),
            "battery_action": battery_action,
            "battery_action_time": peak_reading["date"].strftime("%H:%M"),
            "sustainability_summary": summary,
        })
    except (OSError, ValueError, DatabaseError) as error:
        return jsonify({"error": str(error)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

    