sudo apt update
sudo apt upgrade -y
sudo apt install -y git

sudo raspi-config

git clone https://github.com/matthewcobb/defender-os-node.git /home/pi/defender-os-node
cd /home/pi/defender-os-node
./setup-pi.sh

echo "# sudo nano /boot/firmware/config.txt"
# Audio settings...
dtparam=i2s=on
dtoverlay=hifiberry-dacplus,slave
# HDMI settings...
hdmi_group=2
hdmi_mode=87
hdmi_cvt 1600 600 60 6 0 0 0