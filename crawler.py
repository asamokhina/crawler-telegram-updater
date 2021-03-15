import argparse
import datetime
import logging
import urllib
from contextlib import contextmanager
from random import randint
from time import sleep
from typing import Dict, Optional

import requests
import yaml
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

Link = str 
XPath = str # xpath of the order button which will be checked to deduct availability


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)
logger = logging.getLogger()

def checkout_website(driver, url, xpath) -> str:
    driver.get(url)
    sleep(randint(2, 3))
    (button,) = driver.find_elements_by_xpath(xpath)
    disabled = button.get_attribute("disabled")
    if disabled:
        return ""
    else:
        return f"{url} /n"


@contextmanager
def driver(driver_executable_path):
    display = Display(visible=0, size=(800, 600))
    display.start()
    
    options = Options()
    driver = webdriver.Chrome(options=options, executable_path=driver_executable_path)
    sleep(4)
    
    try:
        yield driver
    finally:
        display.stop()
        driver.quit()


def check_for_updates(crawler_mapping, driver_executable_path) -> str:
    result: str = ""

    with driver(driver_executable_path) as d:
        for url, xpath in crawler_mapping.items():
            try:
                result += checkout_website(d, url, xpath)
            except Exception:
                continue
    

    return result


def check_urls_send_update(crawler_mapping: Dict[Link, XPath], driver_executable_path: str, bot_token: str, chat_id: str):
    """
    A crawler to check webpages to see if a product became available to order.

    This script is written to target some particular pages and their `order` buttons,
    it checks whether the button's boolean parameter `disabled` is `False`. If it is
    the case, the notification to a telegram chat is sent.

    crawler_mapping: mapping of webpage address to the xpath of the button that will be checked.
    driver_executable_path: chrome driver executable path.
    bot_token: telegram bot token provided by Bot Father.
    chat_id: id of the telegram chat to send updates to.

    """
    try:
        update = check_for_updates(crawler_mapping, driver_executable_path)
    except Exception as e:
        logger.warning("Failed to check_for_updates: " + str(e))

    if update:
        logger.info("Got updates")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote_plus(update)}"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            logger.warning("Failed to send a request: " + str(e))

    else:
        logger.info("no news")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    with open(args.config, "r") as stream:
        config = yaml.safe_load(stream)
    check_urls_send_update(**config)


if __name__ == "__main__":
    main()
