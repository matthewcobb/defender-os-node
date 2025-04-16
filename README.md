# defender-os-node
A node car play app built for DefenderOS 

---

## Installation
- Image a pi5 with PiOS Lite 64-bit
- Boot, connect via SSH `ssh pi@defender-os.local`
- Install setup script `scp -r ./scripts/setup-pi.sh pi@<raspberry_pi_ip>:/home/pi/`
- On the pi: `chmod +x setup-pi.sh`
- Run setup `./setup-pi.sh`


mkdir -p ~/.config/openbox
nano ~/.config/openbox/rc.xml

<theme>
    <name>BlackTheme</name>
    <borderWidth>2</borderWidth>
    <titleBarHeight>24</titleBarHeight>
    <borderColor>#000000</borderColor>
    <titleBarColor>#000000</titleBarColor>
    <titleBarTextColor>#FFFFFF</titleBarTextColor>
    <windowColor>#000000</windowColor>
    <windowTextColor>#FFFFFF</windowTextColor>
</theme>

mkdir -p ~/.themes/BlackTheme/openbox-3.5
# Openbox 3.5 theme for BlackTheme
border_width=2
titlebar_height=24
titlebar_color=#000000
titlebar_text_color=#FFFFFF
border_color=#000000
window_color=#000000
window_text_color=#FFFFFF

# ~/.config/openbox/autostart fil
openbox --reconfigure

## 
/etc/xdg/openbox/rc.xml

