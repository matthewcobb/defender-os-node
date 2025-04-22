#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Colors for echoing the steps
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'  # Reset color to default
CLONE_DIR="/home/pi/defender-os-node"

# Update and install dependencies
echo -e "${BLUE}Updating and installing dependencies...${RESET}"
sudo apt update
sudo apt install -y chromium-browser libudev-dev curl python3-pip python3-venv plymouth gpiod swaybg

# # Install Wayfire Plugins
# sudo cp scripts/wayfire/usr/lib/aarch64-linux-gnu/wayfire/libhide-cursor.so /usr/lib/aarch64-linux-gnu/wayfire/libhide-cursor.so
# sudo cp scripts/wayfire/usr/share/wayfire/metadata/hide-cursor.xml /usr/share/wayfire/metadata/hide-cursor.xml
# sudo cp scripts/wayfire/wayfire.ini ~/.config/wayfire.ini

# Install NVM (Node Version Manager)
echo -e "${BLUE}Installing NVM...${RESET}"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
# Ensure NVM is sourced in .bash_profile for the `pi` user

# Load NVM in the current shell
echo -e "${YELLOW}Loading NVM...${RESET}"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

# Install Node.js using NVM
echo -e "${BLUE}Installing Node.js (version 20.x) via NVM...${RESET}"
nvm install 20  # You can change the version number here if needed
nvm use 20      # Set the default version to 20

# Set Node.js version 20 as the default
echo -e "${YELLOW}Setting Node.js version 20 as the default...${RESET}"
nvm alias default 20  # Ensure that version 20 is the default when new sessions start

# Verify the installation
echo -e "${GREEN}Node.js and npm installed successfully.${RESET}"
node -v
npm -v

# Install pm2 via npm
echo -e "${BLUE}Installing pm2...${RESET}"
npm install -g pm2  # Install pm2 globally using npm

# Ensure pm2 is started as a systemd service
echo -e "${YELLOW}Enabling pm2 service on boot...${RESET}"
VERSION=$(node -v)
sudo env PATH=$PATH:/home/pi/.nvm/versions/node/$VERSION/bin /home/pi/.nvm/versions/node/$VERSION/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi

# Ensure NVM is sourced for pm2 in systemd startup
# echo -e "${YELLOW}Configuring pm2 to use NVM...${RESET}"
# Add NVM sourcing to pm2 startup command
# sudo sed -i 's/ExecStart=\/usr\/bin\/node/ExecStart=\/bin\/bash -c "source \/home\/pi\/.bashrc && pm2 start"/g' /etc/systemd/system/pm2-pi.service

# Disable the desktop environment (no graphical environment until Chromium starts)
# echo -e "${YELLOW}Disabling desktop environment...${RESET}"
# sudo systemctl set-default multi-user.target

# Navigate to the app directory and run npm install to install dependencies
echo -e "${BLUE}Installing Node.js dependencies in the app directory...${RESET}"
cd "$CLONE_DIR/app"  # Navigate to the app directory where your app is located
npm install

echo -e "${BLUE}Building app${RESET}"
npm run build

# Start the Node.js app (defender-os-server) using npm run start with pm2
echo -e "${GREEN}Starting Node.js app using pm2...${RESET}"
pm2 start npm --name "defender-os-server" -- run start:prod # Run npm run start using pm2 from the app directory
pm2 save  # Save the pm2 process list to ensure it restarts on boot
cd "$CLONE_DIR" # Return to main directory

# Set up Python virtual environment for defender-os-utilities-server
echo "Setting up Python virtual environment and installing dependencies..."
cd "$CLONE_DIR/python"  # Navigate to the Python directory

# Create virtual environment if it doesn't already exist
if [ ! -d "env" ]; then
    python3 -m venv env

    # Activate the virtual environment
    source env/bin/activate

    # Install the necessary Python packages
    pip install -r requirements.txt

    # Deactivate virtual environment
    deactivate
fi

cd "$CLONE_DIR" # Return to main directory

# Copy defender-os-utilities-server.service from the repo to /etc/systemd/system/
echo -e "${BLUE}Copying defender-os-utilities-server.service to /etc/systemd/system/...${RESET}"
sudo cp "$CLONE_DIR/python/defender-os-utilities-server.service" /etc/systemd/system/defender-os-utilities-server.service

# Enable and start the defender-os-utilities-server service (the Python server must run first)
echo -e "${YELLOW}Enabling and starting defender-os-utilities-server service...${RESET}"
sudo systemctl enable defender-os-utilities-server.service
sudo systemctl start defender-os-utilities-server.service

# Copy defender-os.desktop for autostart
echo -e "${BLUE}Copying defender-os.desktop to autostart...${RESET}"
sudo mkdir -p ~/.config/autostart
sudo cp "$CLONE_DIR/scripts/defender-os.desktop" ~/.config/autostart/defender-os.desktop

# Setup labwc autostart script
echo -e "${BLUE}Setting up labwc autostart for splash screen...${RESET}"
mkdir -p ~/.config/labwc
cp "$CLONE_DIR/scripts/labwc-autostart.sh" ~/.config/labwc/autostart
chmod +x ~/.config/labwc/autostart

# Make splash screen scripts executable
echo -e "${BLUE}Setting up splash screen scripts...${RESET}"
chmod +x "$CLONE_DIR/scripts/display-splash.sh"
chmod +x "$CLONE_DIR/scripts/remove-splash.sh"

# Add smart shutdown service
echo -e "${BLUE}Adding smart shutdown service...${RESET}"
sudo cp "$CLONE_DIR/scripts/carpihat-shutdown.service" /etc/systemd/system/carpihat-shutdown.service
#sudo systemctl enable carpihat-shutdown.service
#sudo systemctl start carpihat-shutdown.service

# Create udev rule for CarLinkit device
echo -e "${BLUE}Creating udev rules for CarLinkit device...${RESET}"
FILE=/etc/udev/rules.d/52-nodecarplay.rules
echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"1314\", ATTR{idProduct}==\"152*\", MODE=\"0660\", GROUP=\"plugdev\"" | sudo tee $FILE

# Check if udev rule creation was successful
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}Permissions created for CarLinkit device${RESET}"
else
    echo -e "${RED}Unable to create permissions for CarLinkit device${RESET}"
fi

# Update bash profile
sudo cp "$CLONE_DIR/scripts/.bash_profile" "/home/pi/.bash_profile"

# plymouth theme
sudo cp -r "$CLONE_DIR/boot/circle_hud" /usr/share/plymouth/themes/
sudo plymouth-set-default-theme -R circle_hud

echo -e "${GREEN}Setup complete! ${RESET}"

echo -e "${YELLOW}Configre boot config...${RESET}"
echo "# sudo nano /boot/firmware/config.txt"
echo "# Audio settings..."
echo "dtparam=i2s=on"
echo "dtoverlay=hifiberry-dacplus,slave"
echo "# HDMI settings..."
echo "hdmi_group=2"
echo "hdmi_mode=87"
echo "hdmi_cvt 1600 600 60 6 0 0 0"
echo "# Latch power"
echo "dtoverlay=gpio-poweroff,gpiopin=25,active_low"
echo "usb_max_current_enable=1" # Enable USB max current, pi5 limits if not powered by usb-c
# Add carPiHat init script
echo -e "${BLUE}Adding carPiHat init script...${RESET}"
echo "You still need to enable the service manually, run:"
echo "sudo systemctl start carpihat-shutdown.service"