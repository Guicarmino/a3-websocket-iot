# app.py
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import datetime
from threading import Event

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "change-this-secret"
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

stop_event = Event()
rolling_temps = []

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def handle_connect():
    try:
        emit("server_status", {
            "message": "connected",
            "average": _average_temp(),
            "count": len(rolling_temps),
            "unit": "C"
        })
    except Exception as e:
        # Do not crash; let the client still remain connected
        emit("server_status", {
            "message": f"connected_with_warning: {str(e)}",
            "average": None,
            "count": len(rolling_temps),
            "unit": "C"
        })

def _generate_temp():
    # Simulate a realistic indoor temperature in Celsius with one decimal place
    return round(random.uniform(18.0, 28.0), 1)

def _average_temp():
    try:
        if not rolling_temps:
            return None
        return round(sum(rolling_temps) / len(rolling_temps), 2)
    except Exception:
        # Guard against unexpected numeric errors
        return None

def emit_temperature_data():
    locations = ["Living Room", "Kitchen", "Bedroom"]
    while not stop_event.is_set():
        data_point = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "temperature": _generate_temp(),
            "location": random.choice(locations)
        }

        # Maintain rolling window to cap memory
        rolling_temps.append(data_point["temperature"])
        if len(rolling_temps) > 1000:
            rolling_temps.pop(0)

        # Emit current sensor reading
        socketio.emit("temperature_data", data_point)
        # Emit current average with error handling
        socketio.emit("average_temperature", {
            "value": _average_temp(),
            "count": len(rolling_temps),
            "unit": "C"
        })

        # Cooperative sleep for Flask-SocketIO
        socketio.sleep(2)

if __name__ == "__main__":
    socketio.start_background_task(emit_temperature_data)
    # Host 0.0.0.0 to support Codespaces port forwarding
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
