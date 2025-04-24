
The package isn't available in your repository. Let's try alternative methods:

1. Create a custom invisible cursor theme:
   ```
   sudo mkdir -p /usr/share/icons/invisible/cursors
   sudo touch /usr/share/icons/invisible/index.theme
   sudo nano /usr/share/icons/invisible/index.theme
   ```

   Add:
   ```
   [Icon Theme]
   Name=Invisible
   Comment=Invisible cursor theme
   ```

   Then create a symlink for the default cursor:
   ```
   cd /usr/share/icons/invisible/cursors
   sudo touch empty
   sudo ln -s empty left_ptr
   ```

2. Edit your rc.xml to use this theme:
   ```
   <mouse>
     <cursor>
       <theme>invisible</theme>
       <size>1</size>
     </cursor>
   </mouse>
   ```

3. Alternative: Try using the environment variable approach:
   ```
   sudo nano /home/pi/.config/labwc/environment
   ```

   Add:
   ```
   WLR_NO_HARDWARE_CURSORS=1
   ```

4. Or you can try installing a different transparent cursor package that might be available:
   ```
   sudo apt-get update
   sudo apt-cache search cursor | grep transparent
   ```

   Look for any transparent cursor package and install it.


## 8.3 custom install
```sudo apt install hwdata libgbm-dev libdisplay-info-dev libseat-dev libinput-dev libpango1.0-dev libpangocairo-1.0-0 libcairo2-dev libglib2.0-dev libpixman-1-dev libxkbcommon-dev liblcms2-dev libxcb-xinput-dev libxcb-errors-dev libxcb-render-util0-dev libxcb-present-dev libxcb-res0-dev libxcb-dri3-dev libxcb-ewmh-dev libxcb-icccm4-dev libxcb-composite0-dev cmake libxml2-dev libliftoff-dev

git clone https://github.com/labwc/labwc
cd labwc/
git clone https://gitlab.freedesktop.org/mesa/drm.git subprojects/libdrm
git clone https://gitlab.freedesktop.org/vyivel/libsfdo.git subprojects/libsfdo
git clone https://gitlab.freedesktop.org/wayland/wayland.git subprojects/wayland
git clone https://gitlab.freedesktop.org/wayland/wayland-protocols.git subprojects/wayland-protocols
meson setup build/
meson compile -C build/```