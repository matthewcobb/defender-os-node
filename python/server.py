from quart import Quart, jsonify, Response
import logging
from gpiozero import CPUTemperature
from renogybt import RoverClient, BatteryClient, LipoModel

dcdc_config =  {
    'type': 'RNG_CTRL',
    'mac_address': 'FC:A8:9B:26:D2:DC',
    'name': 'BT-TH-9B26D2DC',
    'device_id': 255
}

battery_config =  {
    'type': 'RNG_BATT',
    'mac_address': 'AC:4D:16:19:14:1A',
    'name': 'BT-TH-9B26D2DC',
    'device_id': 255
}

# Logging INFO level
# Configure Quart logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('quart.app')
log.setLevel(logging.INFO)

# Create clients
dcdc_client = RoverClient(dcdc_config)
battery_client = BatteryClient(battery_config)

# Flask
app = Quart(__name__)

# Add CORS headers to all responses
@app.after_request
async def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.before_serving
async def before_serving():
    await dcdc_client.connect()
    await battery_client.connect()

async def fetch_renogy_data():
    await dcdc_client.connect()
    await battery_client.connect()

    if not dcdc_client.is_connected or not battery_client.is_connected:
        return jsonify({"error": "RenogyBT not connected"}), 500

    # Compile data request
    if dcdc_client.latest_data and battery_client.latest_data:
        try:
            data = LipoModel(dcdc_client.latest_data, battery_client.latest_data).calculate()
            logging.info(data)
            return data, 200
        except Exception as e:
            logging.error(e)
            return jsonify({"error": e}), 500
    else:
        return jsonify({"error": "No data found!"}), 500

@app.route('/renogy_data', methods=['GET'])
async def dcdc_status():
    return await fetch_renogy_data()

# CPU Temp
@app.route('/cpu_temp', methods=['GET'])
def cpu_temp():
    try:
        cpu = CPUTemperature()
        temp = round(cpu.temperature)
        return {"temp": temp}, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update system endpoint
@app.route('/update_system', methods=['POST'])
async def update_system():
    try:
        import subprocess
        import os

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        # Go up one level to the project root
        project_root = os.path.dirname(script_dir)
        fetch_script = os.path.join(project_root, 'fetch.sh')

        # Run the fetch.sh script and wait for completion
        process = subprocess.run(['/bin/bash', fetch_script],
                                capture_output=True,
                                text=True,
                                check=False)

        # Check if the command was successful
        if process.returncode == 0:
            return {
                "status": "success",
                "message": "Update completed successfully",
                "output": process.stdout
            }, 200
        else:
            logging.error(f"Update script failed with code {process.returncode}")
            logging.error(f"STDOUT: {process.stdout}")
            logging.error(f"STDERR: {process.stderr}")
            return {
                "status": "error",
                "message": "Update failed",
                "returncode": process.returncode,
                "error": process.stderr,
                "output": process.stdout
            }, 500
    except Exception as e:
        logging.error(f"Error running update script: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/close_kiosk', methods=['POST'])
async def close_kiosk():
    try:
        import subprocess

        # Kill Chrome/Chromium processes
        subprocess.run(['pkill', '-f', 'chromium'], check=False)
        subprocess.run(['pkill', '-f', 'chrome'], check=False)

        return {"status": "kiosk closed"}, 200
    except Exception as e:
        logging.error(f"Error closing kiosk: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)