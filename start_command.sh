sudo apt update
sudo apt upgrade -y
sudo apt install -y git
git clone https://github.com/matthewcobb/defender-os-node.git /home/pi/defender-os-node
cd /home/pi/defender-os-node
./setup-pi.sh