# -*- coding: utf-8 -*-
# Example: Scrolling text on display if the string length is major than columns in display.
# Created by Dídac García.

# Import necessary libraries for communication and display use
import lcddriver
import time

# Load the driver and set it to "display"
# If you use something from the driver library use the "display." prefix first
display = lcddriver.Lcd()


def long_string(_display, text, num_line=1, num_cols=20):
    """
    :param _display: lcdrtiver
    :param text: text to be printed
    :param num_line: number of lines to print
    :param num_cols: number of colums to print
    """
    if len(text) > num_cols:
        _display.lcd_display_string(text[:num_cols], num_line)
        time.sleep(1)
        for i in range(len(text) - num_cols + 1):
            text_to_print = text[i:i + num_cols]
            _display.lcd_display_string(text_to_print, num_line)
            time.sleep(0.2)
        time.sleep(1)
    else:
        _display.lcd_display_string(text, num_line)


try:
    print("Press CTRL + C for stop this script!")
    long_string(display, "Hello again. This is a long text.", 2)
    display.lcd_clear()
    time.sleep(1)

except KeyboardInterrupt:
    print("Cleaning up!")
    display.lcd_clear()
