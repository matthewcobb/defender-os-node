"""
Service to handle splash screen removal
"""
import os
import subprocess
import sys
import logging
import signal

def remove_splash_screen():
    """
    Remove the splash screen
    """
    # First try to kill by PID file
    try:
        if os.path.exists('/tmp/splash-pid.txt'):
            with open('/tmp/splash-pid.txt', 'r') as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, signal.SIGTERM)
                logging.info(f"Killed splash screen with PID {pid}")
            except ProcessLookupError:
                logging.info(f"No process with PID {pid}")
            except Exception as e:
                logging.error(f"Error killing splash process: {str(e)}")

            # Remove the PID file
            try:
                os.remove('/tmp/splash-pid.txt')
            except Exception:
                pass

            return {"status": "success", "message": f"Removed splash screen via PID file"}, 200
        else:
            # As a last resort, try to find and kill any Python splash process
            try:
                subprocess.run(
                    ["pkill", "-f", "python.*splash-overlay.py"],
                    check=False
                )
                return {"status": "success", "message": "Attempted to kill splash screen processes"}, 200
            except Exception as e:
                logging.error(f"Error killing splash processes: {str(e)}")

        return {"status": "warning", "message": "No splash screen found to remove"}, 200

    except Exception as e:
        logging.error(f"Error removing splash screen: {str(e)}")
        return {"status": "error", "message": f"Failed to remove splash screen: {str(e)}"}, 500