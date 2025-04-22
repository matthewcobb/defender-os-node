#!/usr/bin/env python3
import sys
import gi
import os
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib

# Path to the default image
DEFAULT_IMAGE_PATH = "/home/pi/defender-os-node/boot/background.jpg"

# Fallback display size if we can't detect monitor
FALLBACK_WIDTH = 1600
FALLBACK_HEIGHT = 600

class SplashWindow(Gtk.Window):
    def __init__(self, image_path=None):
        Gtk.Window.__init__(self, title="Splash")

        # Check if either image exists before proceeding
        has_image = False
        if image_path and os.path.exists(image_path):
            print(f"Found provided image: {image_path}")
            self.image_path = image_path
            has_image = True
        elif os.path.exists(DEFAULT_IMAGE_PATH):
            print(f"Found default image: {DEFAULT_IMAGE_PATH}")
            self.image_path = DEFAULT_IMAGE_PATH
            has_image = True

        # Exit if no image is found
        if not has_image:
            print("No image found. Exiting without showing splash.")
            sys.exit(0)

        # Make fullscreen and set priority
        self.fullscreen()
        self.set_keep_above(True)

        # Set black background using CSS
        self._setup_css()

        # Create a container
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        # Set up event box to capture clicks
        event_box = Gtk.EventBox()
        event_box.connect("button-press-event", self.on_click)
        self.box.pack_start(event_box, True, True, 0)

        # Try to load the image
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.image_path)

            # Get display size with better error handling
            width, height = self._get_display_size()
            print(f"Using display size: {width}x{height}")

            # Scale image
            pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

            # Create image widget
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            event_box.add(image)

        except Exception as e:
            print(f"Error loading image: {e}")
            sys.exit(1)

        # Save PID to file for later cleanup
        with open('/tmp/splash-pid.txt', 'w') as f:
            f.write(str(os.getpid()))

    def _get_display_size(self):
        """Get display dimensions with fallbacks for Wayland"""
        try:
            # Try modern approach first
            display = Gdk.Display.get_default()
            if display:
                monitor = display.get_primary_monitor()
                if monitor:
                    geometry = monitor.get_geometry()
                    return geometry.width, geometry.height

            # Fallback to screen approach
            screen = Gdk.Screen.get_default()
            if screen:
                width = screen.get_width()
                height = screen.get_height()
                if width > 0 and height > 0:
                    return width, height

            # If we're here, try to get current window size
            allocation = self.get_allocation()
            if allocation.width > 100 and allocation.height > 100:
                return allocation.width, allocation.height

        except Exception as e:
            print(f"Error detecting screen size: {e}")

        # Final fallback to hardcoded values
        print(f"Using fallback display size: {FALLBACK_WIDTH}x{FALLBACK_HEIGHT}")
        return FALLBACK_WIDTH, FALLBACK_HEIGHT

    def on_click(self, widget, event):
        """Exit when clicked anywhere"""
        print("Splash screen clicked, exiting...")
        self.cleanup()
        Gtk.main_quit()

    def cleanup(self):
        """Remove PID file on exit"""
        try:
            if os.path.exists('/tmp/splash-pid.txt'):
                os.remove('/tmp/splash-pid.txt')
        except Exception as e:
            print(f"Error cleaning up: {e}")

    def _setup_css(self):
        # Create CSS provider
        css_provider = Gtk.CssProvider()
        css = """
        window {
            background-color: #000000;
        }
        """
        css_provider.load_from_data(bytes(css.encode()))

        # Apply CSS to the application
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

if __name__ == "__main__":
    # Get image path from arguments if provided
    image_path = None
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

    # Set up proper exit handling
    win = SplashWindow(image_path)
    win.connect("destroy", lambda x: Gtk.main_quit())

    # Handle Ctrl+C gracefully
    def signal_handler(sig):
        win.cleanup()
        Gtk.main_quit()

    # Show window and start main loop
    win.show_all()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        win.cleanup()
        sys.exit(0)