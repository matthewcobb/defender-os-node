# DefenderOS Node

A Node.js based CarPlay application built for Land Rover Defenders. This project integrates CarPlay functionality with Raspberry Pi, providing a custom infotainment system for Defender vehicles.

## Overview

DefenderOS is a complete infotainment solution that includes:

- Apple CarPlay integration via node-CarPlay
- Battery monitoring via Renogy BT integration
- GPIO interface for vehicle integration (reverse camera, etc.)
- Modern Vue.js-based UI
- Python backend for system utilities

## Hardware Requirements

- Raspberry Pi 5 (recommended)
- CarLinkit wireless/wired CarPlay adapter
- Display (HDMI)
- Optional: Renogy BT-compatible battery monitor
- Optional: GPIO connections for reverse camera integration

## Installation

### Quick Start

1. Image a Raspberry Pi 5 with Raspberry Pi OS Lite 64-bit
2. Boot and connect via SSH: `ssh pi@defender-os.local` or `ssh pi@<raspberry_pi_ip>`
3. Install the setup script:
   ```
   scp -r ./setup-pi.sh pi@<raspberry_pi_ip>:/home/pi/
   ```
4. On the Pi, make the script executable:
   ```
   chmod +x setup-pi.sh
   ```
5. Run the setup script:
   ```
   ./setup-pi.sh
   ```

### Manual Configuration

After running the setup script, you may need to configure these settings:

#### Audio Configuration

Edit `/boot/firmware/config.txt` and add:
```
# Audio settings
dtparam=i2s=on
dtoverlay=hifiberry-dacplus,slave
```

#### Display Configuration

Edit `/boot/firmware/config.txt` and add:
```
# HDMI settings
hdmi_group=2
hdmi_mode=87
hdmi_cvt 1600 600 60 6 0 0 0
```

#### Power Management

Edit `/boot/firmware/config.txt` and add:
```
# Latch power
dtoverlay=gpio-poweroff,gpiopin=25,active_low
usb_max_current_enable=1
```

#### Enable the shutdown service

```
sudo systemctl enable carpihat-shutdown.service
sudo systemctl start carpihat-shutdown.service
```

## System Architecture

- **Frontend**: Vue.js-based UI in the `app` directory
- **Backend**: Express.js server serving the Vue app
- **Utilities**: Python-based services for GPIO, system monitoring, and battery management

## Development

To develop locally:

1. In the app directory:
   ```
   npm i
   npm start
   ```

2. For the Python utilities server:
   ```
   cd python
   python -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   python main.py
   ```

## License

This project is proprietary and not licensed for public use without explicit permission.


