import asyncio
import json
import multiprocessing
import re
from pathlib import Path
from typing import Dict, List

import feedparser

from libs import lcddriver
from libs.pigpio_encoder import Rotary

# config
CONFIG_FILE_Path = Path("db", "config.json")
if not CONFIG_FILE_Path.is_file():
    CONFIG_FILE_Path.touch()
# "database"
DB_FILE_Path = Path("db", "coffee.log")
if not DB_FILE_Path.is_file():
    DB_FILE_Path.touch()
# rss
RSS_URL = "http://www.tagesschau.de/xml/rss2/"


def prettyfy_rss_string(input_str):
    # print german literals the right way
    input_str = re.sub("ä", "ae", input_str)
    input_str = re.sub("ö", "oe", input_str)
    input_str = re.sub("ü", "ue", input_str)
    input_str = re.sub("Ä", "Ae", input_str)
    input_str = re.sub("Ö", "Oe", input_str)
    input_str = re.sub("Ü", "Ue", input_str)
    input_str = re.sub("ß", "ss", input_str)
    # remove Liveblog-announcement from Feed
    input_str = re.sub(r"Liveblog: [+]+ ", "", input_str)
    input_str = re.sub(r"[+]+ ", "", input_str)
    # remove non-ascii characters
    return input_str.encode('ascii', 'replace').decode()


class CoffeeTerminal:
    def __init__(self, coffee_lcd: lcddriver.Lcd):
        print("starting setup")
        # setup lcd
        self.lcd = coffee_lcd
        # setup rss
        self.rss_text = "Loading Tagesschau"
        # load config
        with open(CONFIG_FILE_Path) as config_file:
            config = json.load(config_file)
        self.selected_idex: int = int(config["selected_index"])
        self.names: List[str] = list(set(config["names"]))
        if len(self.names) == 0:
            self.names = ["default"]
        self.coffee_balance: Dict[str, int] = config["coffee_on_last_restart"]
        self.confirmation_page = False
        self.confirmation_index = 0

        # initialise coffee_balance
        if self.coffee_balance.keys() != set(self.names):
            for name in self.names:
                if name not in self.coffee_balance.keys():
                    print(f"initialised {name}")
                    self.coffee_balance[name] = 0
        # load "Database"
        with open(DB_FILE_Path) as db_file:
            served_coffees = db_file.readlines()
            for line in served_coffees:
                if line in self.coffee_balance.keys():
                    self.coffee_balance[line] += 1
                else:
                    print(f"coffee.log line {line} could not be read")

        # override old coffee file
        with open(DB_FILE_Path, "w") as db_file:
            db_file.write("")

        # writeback to config
        with open(CONFIG_FILE_Path, "w") as config_file:
            config = {
                "selected_index": self.selected_idex,
                "names": self.names,
                "coffee_on_last_restart": self.coffee_balance,
            }
            json.dump(config, config_file)

        if multiprocessing.cpu_count() < 2:  # if rasperry
            my_rotary = Rotary(clk_gpio=5, dt_gpio=6, sw_gpio=12)
            my_rotary.setup_rotary(up_callback=self.up_callback, down_callback=self.down_callback, debounce=300)
            my_rotary.setup_switch(sw_long_callback=self.switch_pressed, long_press=True, debounce=300)

        self.switchloop = asyncio.get_event_loop()
        print("setup done")

    async def print_rss(self):
        print("rss loop")
        count = 0
        while True:
            count -= 1
            if count <= 0:
                await self.update_rss()
                count = 40
            if len(self.rss_text) > 20:
                await self.lcd.lcd_display_string(self.rss_text[:20], 0)
                await asyncio.sleep(2)
                for i in range(len(self.rss_text) - 20 + 1):
                    text_to_print = self.rss_text[i:i + 20]
                    await self.lcd.lcd_display_string(text_to_print, 0)
                    await asyncio.sleep(0.4)
                await asyncio.sleep(3)
            else:
                await self.lcd.lcd_display_string(self.rss_text, 0)
                await asyncio.sleep(4)

    async def update_rss(self):
        d = feedparser.parse(RSS_URL)["entries"]
        titeles = [entry['title'] for entry in d]
        self.rss_text = prettyfy_rss_string("   ---   ".join(titeles))

    async def dial_pressed(self):
        if self.confirmation_page:
            # buy
            selected_name = self.names[self.selected_idex]
            new_balance = self.coffee_balance[selected_name] + 1
            with open(DB_FILE_Path, "a+") as db:
                db.write(selected_name + "\n")
            self.coffee_balance[selected_name] = new_balance
            # print balance
            await self.lcd.lcd_display_string("New Balance:", 1)
            await self.lcd.lcd_display_string(str(new_balance)[:20], 1)
            await asyncio.sleep(3)
            # print thank you message
            await self.lcd.lcd_display_string("Thank you for", 1)
            await self.lcd.lcd_display_string("choosing the", 2)
            await self.lcd.lcd_display_string("Coffee-Terminal", 3)
            await asyncio.sleep(2)
            self.confirmation_page = False
            await self.display_index()
        else:
            self.confirmation_page = True
            await self.display_confirmation()

    async def dial_turned(self, i):
        if not self.confirmation_page:
            self.selected_idex = (self.selected_idex + i) % len(self.names)
            await self.display_index()
        else:
            self.confirmation_index = (self.confirmation_index + i) % 2
            await self.display_confirmation()

    def switch_pressed(self):
        self.switchloop.create_task(self.dial_pressed())

    def up_callback(self):
        self.switchloop.create_task(self.dial_turned(+1))

    def down_callback(self):
        self.switchloop.create_task(self.dial_turned(-1))

    def generate_name_str(self, prefix, name):
        balance = str(self.coffee_balance[name])
        return (prefix + name + (" " * 20))[:(20 - len(balance))] + balance

    async def display_index(self):
        names = [self.names[(self.selected_idex + i) % len(self.names)] for i in range(-1, 2)]
        await self.lcd.lcd_display_string(self.generate_name_str("  ", names[0]), 1)
        await self.lcd.lcd_display_string(self.generate_name_str("> ", names[1]), 2)
        await self.lcd.lcd_display_string(self.generate_name_str("  ", names[2]), 3)

    async def display_confirmation(self):
        selectors = ["  ", "> "]
        if self.confirmation_index:
            selectors.reverse()
        await self.lcd.lcd_display_string(self.generate_name_str("* ", self.names[self.selected_idex]), 1)
        await self.lcd.lcd_display_string(selectors.pop() + "Confirm", 2)
        await self.lcd.lcd_display_string(selectors.pop() + "Cancel", 3)


async def main(lcd_terminal):
    await lcd_terminal.lcd_clear()
    await lcd_terminal.lcd_backlight(True)
    terminal = CoffeeTerminal(lcd_terminal)
    await asyncio.create_task(terminal.print_rss())
    while True:
        await asyncio.sleep(10)


if __name__ == "__main__":
    lcd = lcddriver.LcdDummy()
    if multiprocessing.cpu_count() < 2:  # if rasperry
        lcd = lcddriver.Lcd(debug=True)
    try:
        asyncio.run(main(lcd))
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        asyncio.run(lcd.lcd_clear())
        asyncio.run(lcd.lcd_display_string("Sorry for the", 0))
        asyncio.run(lcd.lcd_display_string("inconvenience.", 1))
        asyncio.run(lcd.lcd_display_string("Maintenance in", 2))
        asyncio.run(lcd.lcd_display_string("progress...", 3))
