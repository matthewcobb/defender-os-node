# Raspberry Pi OS Lite Configuration Files

This directory contains configuration files for setting up Raspberry Pi OS Lite with Wayfire and Chrome kiosk mode.

## Files

- `wayfire-autostart`: Script that runs when Wayfire starts. It launches the Chrome browser in kiosk mode.
- `bash-profile`: Custom .bash_profile that automatically starts Wayfire when logging in on tty1.
- `wayfire.ini`: Wayfire configuration file with the hide-cursor plugin enabled.

## Usage

These files are used by the `setup-pi-lite.sh` script in the root directory. The script copies these files to their appropriate locations during setup.