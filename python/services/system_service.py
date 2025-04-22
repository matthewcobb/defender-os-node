"""
Service for system operations like CPU temperature, updates, and kiosk management
"""
import logging
import subprocess
import os
import asyncio
from gpiozero import CPUTemperature
from config.settings import PROJECT_ROOT, APP_DIR
from flask import jsonify

# Initialize update status
update_status = {
    "overall_status": "not_started",
    "steps": [],
    "current_step": -1,
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
    """Run the system update steps and report progress"""
    update_steps = [
        {"name": "git_pull", "status": "pending", "message": "Pulling latest changes..."},
        {"name": "npm_install", "status": "pending", "message": "Installing dependencies..."},
        {"name": "npm_build", "status": "pending", "message": "Building application..."},
        {"name": "restart", "status": "pending", "message": "Restarting services..."}
    ]

    try:
        # Store global update status
        global update_status
        update_status = {
            "overall_status": "in_progress",
            "steps": update_steps,
            "current_step": 0,
            "error": None
        }

        # Step 1: Git pull
        update_status["current_step"] = 0
        update_status["steps"][0]["status"] = "in_progress"
        logging.info("Running git pull...")

        process = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False
        )

        if process.returncode != 0:
            raise Exception(f"Git pull failed: {process.stderr}")

        update_status["steps"][0]["status"] = "complete"
        update_status["steps"][0]["output"] = process.stdout
        logging.info("Git pull completed successfully")

        # Step 2: npm install
        update_status["current_step"] = 1
        update_status["steps"][1]["status"] = "in_progress"
        logging.info("Running npm install...")

        # Get environment with PATH
        env = os.environ.copy()

        # Run npm install with a login shell that will load .bashrc/.bash_profile
        process = subprocess.run(
            ["/bin/bash", "-l", "-c", f"cd {APP_DIR} && npm install"],
            capture_output=True,
            text=True,
            check=False,
            env=env
        )

        if process.returncode != 0:
            raise Exception(f"npm install failed: {process.stderr}")

        update_status["steps"][1]["status"] = "complete"
        update_status["steps"][1]["output"] = process.stdout
        logging.info("npm install completed successfully")

        # Step 3: npm run build
        update_status["current_step"] = 2
        update_status["steps"][2]["status"] = "in_progress"
        logging.info("Running npm run build...")

        # Run npm build with a login shell that will load .bashrc/.bash_profile
        process = subprocess.run(
            ["/bin/bash", "-l", "-c", f"cd {APP_DIR} && npm run build"],
            capture_output=True,
            text=True,
            check=False,
            env=env
        )

        if process.returncode != 0:
            raise Exception(f"npm run build failed: {process.stderr}")

        update_status["steps"][2]["status"] = "complete"
        update_status["steps"][2]["output"] = process.stdout
        logging.info("npm run build completed successfully")

        # Step 4: restart services
        update_status["current_step"] = 3
        update_status["steps"][3]["status"] = "in_progress"
        logging.info("Restarting services...")

        # Run pm2 restart with a login shell that will load .bashrc/.bash_profile
        process = subprocess.run(
            ["/bin/bash", "-l", "-c", "pm2 restart defender-os-server"],
            capture_output=True,
            text=True,
            check=False,
            env=env
        )

        if process.returncode != 0:
            raise Exception(f"Service restart failed: {process.stderr}")

        update_status["steps"][3]["status"] = "complete"
        update_status["steps"][3]["output"] = process.stdout
        logging.info("Services restarted successfully")

        # Update overall status
        update_status["overall_status"] = "complete"
        logging.info("Update process completed successfully")

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Update failed: {error_msg}")

        # Mark current step as failed
        if "current_step" in update_status:
            current_step = update_status["current_step"]
            if current_step < len(update_status["steps"]):
                update_status["steps"][current_step]["status"] = "failed"
                update_status["steps"][current_step]["error"] = error_msg

        update_status["overall_status"] = "failed"
        update_status["error"] = error_msg

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