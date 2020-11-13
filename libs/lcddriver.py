# Driver library for LCD display. Provided by Ryanteck LTD.
# The procedures below can all be called in your own code!
# You can just stick to the print string one though ;-)

# This is the driver library for the LCD display
# It contains some functions that you can call in your own program
# Just remember that in order to use it you have to import it
# You can do that with the line: import lcddriver
# Make sure that lcddriver is in the same directory though!
# Credit for this code goes to "natbett" of the Raspberry Pi Forum 18/02/13

# Backlight: Enhanced by TOMDENKT - backlight control (on/off)
# If lcddriver.py is NOT in same folder with your scripts,
# set path to lcddriver IN YOUR script such as
# import sys
# sys.path.append("/home/pi/lcd") # example, path to lcddriver.py
import asyncio
from time import sleep

from libs import i2c_lib

# LCD Address
# Usually you will have to use one of the two provided values below.
# If you prefer, you can check your LCD address with the command: "sudo i2cdetect -y 1"
# This is a common LCD address.
ADDRESS = 0x27
# This is another common LCD address.
# ADDRESS = 0x3f

# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100  # Enable bit
Rw = 0b00000010  # Read/Write bit
Rs = 0b00000001  # Register select bit


class Lcd:
    # initializes objects and lcd
    def __init__(self, debug=False):
        self.lock = asyncio.Lock()
        self.lcd_device = i2c_lib.I2cDevice(ADDRESS)
        self.debug = debug
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x02)

        self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
        self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        sleep(0.2)

    # clocks EN to latch command
    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
        sleep(.0005)
        self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
        sleep(.0001)

    def lcd_write_four_bits(self, data):
        self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
        self.lcd_strobe(data)

    # write a command to lcd
    def lcd_write(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # put string function
    async def lcd_display_string(self, string, line):
        string = (string + (" " * 20))[:20]
        if self.debug:
            print(f"{line}: {string} [len: {len(string)}]")
        async with self.lock:
            if line % 4 + 1 == 1:
                self.lcd_write(0x80)
            if line % 4 + 1 == 2:
                self.lcd_write(0xC0)
            if line % 4 + 1 == 3:
                self.lcd_write(0x94)
            if line % 4 + 1 == 4:
                self.lcd_write(0xD4)

            for char in string:
                self.lcd_write(ord(char), Rs)

    # clear lcd and set to home
    async def lcd_clear(self):
        if self.debug:
            print(f"Cleared Screen")
        async with self.lock:
            self.lcd_write(LCD_CLEARDISPLAY)
            self.lcd_write(LCD_RETURNHOME)

    async def lcd_backlight(self, state):
        async with self.lock:
            if state:
                self.lcd_device.write_cmd(LCD_BACKLIGHT)
            else:
                self.lcd_device.write_cmd(LCD_NOBACKLIGHT)


class LcdDummy:

    def __init__(self, debug=False):
        self.lock = asyncio.Lock()
        self.debug = debug

    def lcd_strobe(self, data):
        pass

    def lcd_write_four_bits(self, data):
        pass

    def lcd_write(self, cmd, mode=0):
        pass

    async def lcd_display_string(self, string, line):
        async with self.lock:
            print(f"{line}: {string}")

    async def lcd_clear(self):
        async with self.lock:
            print("cleared screen")

    async def lcd_backlight(self, state):
        async with self.lock:
            print(f"backlight={state}")
