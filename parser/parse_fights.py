import requests
from bs4 import PageElement
from bs4 import BeautifulSoup
import pandas as pd
from random import randint

MAIN_URL = "https://ufc.ru"
EVENTS_URL = "https://ufc.ru/events"
FIGHTERS_DF = pd.read_csv("data/fighters.csv", index_col=[0])
FIGHTERS_DATA_DF = pd.read_csv("data/fighters_data.csv", index_col=[0])

# на сайте представлена такая структура: 1 event = ссылка на чемпионат с множеством боев, поэтому парсятся сначала event
def parse_events () -> list:
    response = requests.get(EVENTS_URL+"#events-list-past")
    soup = BeautifulSoup(response.text, "html.parser")

    Urls = []

    # на странице с ?page>=36 чемпионаты с теми бойцами, которых нету в рейтинге UFC
    for i in range(35+1):
        current_response = requests.get(f"{EVENTS_URL}?page={i}#events-list-past")
        soup = BeautifulSoup(current_response.text, "html.parser")

        buttons = soup.find_all(name="a", attrs={"class": "e-button--white"})
        for link in buttons:
            if link.findNext("span").get_text().strip().lower() == "итоги":
                Urls.append(MAIN_URL+link.get("href"))        