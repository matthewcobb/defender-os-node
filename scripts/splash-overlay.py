#!/usr/bin/env python3
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk

class SplashWindow(Gtk.Window):
    def __init__(self, image_path):
        Gtk.Window.__init__(self, title="Splash")

        # Make fullscreen and always on top
        self.fullscreen()
        self.set_keep_above(True)

        # Set black background
        self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))

        # Load the image
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)

            # Get screen size
            screen = self.get_screen()
            monitor = screen.get_monitor_at_window(screen.get_active_window())
            geometry = screen.get_monitor_geometry(monitor)

            # Scale image to fit screen
            width, height = geometry.width, geometry.height
            pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

            # Create image widget
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            self.add(image)

        except Exception as e:
            print(f"Error loading image: {e}")
            label = Gtk.Label(label="Error loading splash image")
            self.add(label)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: splash-overlay.py IMAGE_PATH")
        sys.exit(1)

    image_path = sys.argv[1]
    win = SplashWindow(image_path)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()