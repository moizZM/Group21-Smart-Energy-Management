from flask import Flask, jsonify

from database_reader import load_dashboard_readings
from dashboard.dashboard_data import DashboardData
from src.data_base.database_manager import DatabaseError


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)