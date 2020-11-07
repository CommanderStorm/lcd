import asyncio
import json
from pathlib import Path
from typing import Dict, List

import feedparser

import lcddriver

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


class CoffeTerminal:
    def __init__(self, coffee_lcd: lcddriver.Lcd):
        print("starting setup")
        self.rss_text = "Loading Tagesschau"
        self.lcd = coffee_lcd
        # load config
        with open(CONFIG_FILE_Path) as config_file:
            config = json.load(config_file)
        self.selected_idex: int = int(config["selected_idex"])
        self.names: List[str] = list(set(config["names"]))
        self.coffee: Dict[str, int] = config["coffee_on_last_restart"]

        # initialise coffes
        if self.coffee.keys() != set(self.names):
            for name in self.names:
                if name not in self.coffee.keys():
                    print(f"initialised {name}")
                    self.coffee[name] = 0
        # load "Database"
        with open(DB_FILE_Path) as db_file:
            served_coffees = db_file.readlines()
            for line in served_coffees:
                if line in self.coffee.keys():
                    self.coffee[line] += 1
                else:
                    print(f"coffee.log line {line} could not be read")

        # override old coffee file
        with open(DB_FILE_Path, "w") as db_file:
            db_file.write("")

        # writeback to config
        with open(CONFIG_FILE_Path, "w") as config_file:
            config = {
                "selected_idex": self.selected_idex,
                "names": self.names,
                "coffee_on_last_restart": self.coffee,
            }
            json.dump(config, config_file)

        print("starting main loop")
        asyncio.run(self.main())

    async def main(self):
        await self.update_rss()
        await self.main_ui()
        await self.print_rss()

    async def print_rss(self):
        while True:
            if len(self.rss_text) > 20:
                self.lcd.lcd_display_string(self.rss_text[:20], 0)
                await asyncio.sleep(2)
                for i in range(len(self.rss_text) - 20 + 1):
                    text_to_print = self.rss_text[i:i + 20]
                    self.lcd.lcd_display_string(text_to_print, 0)
                    await asyncio.sleep(0.2)
                await asyncio.sleep(3)
            else:
                self.lcd.lcd_display_string(self.rss_text, 0)
                await asyncio.sleep(4)

    async def update_rss(self):
        while True:
            d = feedparser.parse(RSS_URL)["entries"]
            titeles = [entry['title'] for entry in d]
            self.rss_text = "   ---   ".join(titeles).encode('ascii', 'replace').decode()
            await asyncio.sleep(10 * 60)

    async def main_ui(self):
        pass


if __name__ == "__main__":
    lcd = lcddriver.Lcd()
    lcd.lcd_clear()
    lcd.lcd_backlight(False)

    try:
        terminal = CoffeTerminal(lcd)
    except KeyboardInterrupt:
        pass
    finally:
        lcd.lcd_clear()
        lcd.lcd_display_string("Sorry for the", 0)
        lcd.lcd_display_string("inconvinience.", 1)
        lcd.lcd_display_string("Maintenance in", 2)
        lcd.lcd_display_string("progress...", 3)
