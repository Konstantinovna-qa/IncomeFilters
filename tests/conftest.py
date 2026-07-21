import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture
def driver():
    """Создаёт и после сценария закрывает независимый экземпляр Chrome."""
    options = Options()
    if os.getenv("HH_HEADLESS", "true").lower() == "true":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--lang=ru-RU")
    options.add_argument("--disable-notifications")

    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(0)
    yield browser
    browser.quit()
