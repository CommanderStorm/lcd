# If lcddriver.py is NOT in same folder with your scripts,
# uncomment below and set path to lcddriver, e.g. "/home/pi/lcd"
# import sys
# sys.path.append("/home/pi/lcd") # example, path to lcddriver.py

import lcddriver

display = lcddriver.Lcd()

try:
    print("Press CTRL + C to quit program")
    while True:
        display.lcd_display_string("I am a display! ", 1)
        display.lcd_display_string("Demo Backlight", 2)
        display.lcd_clear()
        display.lcd_backlight(0)

except KeyboardInterrupt:
    print("Exit and cleaning up!")
    display.lcd_clear()
    display.lcd_backlight(1)
