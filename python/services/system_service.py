"""
Service for system operations like CPU temperature, updates, and kiosk management
"""
import logging
import subprocess
import os
import asyncio
import re
from gpiozero import CPUTemperature
from config.settings import PROJECT_ROOT, APP_DIR
from flask import jsonify

# Path to the fetch.sh script
FETCH_SCRIPT = os.path.join(PROJECT_ROOT, "fetch.sh")

# Initialize update status with a simpler structure
update_status = {
    "overall_status": "not_started",
    "logs": [],
    "current_step": None,
    "error": None
}

def get_cpu_temperature():
    """Get the CPU temperature"""
    try:
        cpu = CPUTemperature()
        temp = round(cpu.temperature)
        return {"temp": temp}, 200
    except Exception as e:
        logging.error(f"Error getting CPU temperature: {str(e)}")
        return {"error": str(e)}, 500

async def close_kiosk():
    """Close the Chrome/Chromium kiosk browser"""
    try:
        # Kill Chrome/Chromium processes
        subprocess.run(['pkill', '-f', 'chromium'], check=False)
        subprocess.run(['pkill', '-f', 'chrome'], check=False)

        return {"status": "kiosk closed"}, 200
    except Exception as e:
        logging.error(f"Error closing kiosk: {str(e)}")
        return {"error": str(e)}, 500

async def start_system_update():
    """Initiate system update process"""
    try:
        # Start the update process in a background task
        asyncio.create_task(run_system_update())
        return {"status": "initiated", "message": "Update process started"}, 200
    except Exception as e:
        logging.error(f"Error initiating update: {str(e)}")
        return {"error": str(e)}, 500

async def run_system_update():
    """Run the system update by calling the fetch.sh script and relaying its output"""
    global update_status

    # Reset update status
    update_status = {
        "overall_status": "in_progress",
        "logs": [],
        "current_step": None,
        "error": None
    }

    logging.info(f"Starting system update using {FETCH_SCRIPT}")

    try:
        # Create a process to run the fetch.sh script
        process = await asyncio.create_subprocess_exec(
            FETCH_SCRIPT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Regular expression to extract progress information
        progress_pattern = re.compile(r'\[PROGRESS:(\w+):(\w+):(\w+)\]')

        # Process stdout in real-time
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break

            line = line_bytes.decode('utf-8').strip()

            # Add line to logs
            update_status["logs"].append(line)
            logging.info(f"Update output: {line}")

            # Check for progress markers
            match = progress_pattern.search(line)
            if match:
                action_type = match.group(1)
                step_name = match.group(2)
                status = match.group(3)

                if action_type == "STEP" and status == "started":
                    # Update current step when a new step starts
                    update_status["current_step"] = {
                        "name": step_name,
                        "status": "in_progress",
                        "message": line.split("] ")[1] if "] " in line else ""
                    }

                elif action_type == "OVERALL" and status in ["completed", "failed"]:
                    update_status["overall_status"] = "complete" if status == "completed" else "failed"

        # Process stderr if there's any
        stderr_data = await process.stderr.read()
        stderr_text = stderr_data.decode('utf-8').strip()
        if stderr_text:
            logging.error(f"Update stderr: {stderr_text}")
            update_status["logs"].append(f"❌ Error: {stderr_text}")
            if update_status["overall_status"] != "failed":
                update_status["overall_status"] = "failed"
                update_status["error"] = stderr_text

        # Wait for process to complete
        await process.wait()

        # If process exited with non-zero and we haven't already set a failure status
        if process.returncode != 0 and update_status["overall_status"] != "failed":
            error_msg = f"Update process exited with code {process.returncode}"
            update_status["overall_status"] = "failed"
            update_status["error"] = error_msg
            update_status["logs"].append(f"❌ {error_msg}")
            logging.error(error_msg)

        logging.info(f"Update process completed with status: {update_status['overall_status']}")

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error running update script: {error_msg}")
        update_status["overall_status"] = "failed"
        update_status["error"] = error_msg
        update_status["logs"].append(f"❌ {error_msg}")

def get_update_status():
    """Get the current status of the system update"""
    return update_status, 200

async def remove_splash_screen():
    """Remove the splash screen that's displayed during boot"""
    try:
        import subprocess
        subprocess.run(['/home/pi/defender-os-node/scripts/remove-splash.sh'], check=True)
        return jsonify({
            'status': 'success',
            'message': 'Splash screen removed'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to remove splash screen: {str(e)}'
        })