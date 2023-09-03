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

def check_fighters (names: list[str], urls: list[str]) -> tuple[list[str|int]]:
    # В ID_list добавляются идентификаторы бойцов, которые нашлись в базе
    # В URL_list добавляются ссылки на тех бойцов, которых в базе нет
    # ссылки из URL_list будут парситься отдельно функцией parse_one_fighter() из parse_fighters.py
    # возвращает кортеж с массивами идентификаторов бойцов и ссылок на тех, кого надо парсить
    ID_list = []
    URL_list = []

    for index, name in enumerate(names):
        FighterID = FIGHTERS_DF[FIGHTERS_DF["Name"] == name]["FighterID"].values
    
        if FighterID.size > 0:             
            if FIGHTERS_DATA_DF[FIGHTERS_DATA_DF["FighterID"] == FighterID[0]]["FighterID"].values.size > 0:
                ID_list.append(FighterID[0])
            else:
                URL_list.append(urls[index])

        else: URL_list.append(urls[index])

    return (ID_list, URL_list)


def parse_fights ():
    LINKS_EVENTS = [] # parse_events()  
    # убрать после завершения работы    
    with open("events.txt", "r", encoding="utf8") as f:
        for line in f.readlines():
            LINKS_EVENTS.append(line.strip())

    for url in LINKS_EVENTS:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        fight_cards_ResultSet = soup.find(name="ul", attrs={"class": "l-listing__group--bordered"}).find_all(name="li")
        fight_cards = []

        for card in fight_cards_ResultSet:
            # парсинг имён двух бойцов. Далее по ним ведется поиск в fighters.csv 
            # -> если находится - возвращает FighterID
            # -> если не находится, то пытается спарсить данные бойца. 
            # Если получается -> заносит бойца в fighters.csv и fighters_data.csv -> возвращает FighterID
            fighter_names = []
            fighter_names.append(soup.find(name="div", attrs={"class": "c-listing-fight__corner-name--red"}).get_text().strip().replace("\n", " "))
            fighter_names.append(soup.find(name="div", attrs={"class": "c-listing-fight__corner-name--blue"}).get_text().strip().replace("\n", " "))

            fighter_urls = []
            fighter_urls.append(soup.find(name="div", attrs={"class": "c-listing-fight__corner-name--red"}).find(name="a").get("href"))
            fighter_urls.append(soup.find(name="div", attrs={"class": "c-listing-fight__corner-name--blue"}).find(name="a").get("href"))

            print(fighter_names, fighter_urls, sep=", ")
            # check_fighters(fighter_names, fighter_urls)

            
            break

        break
            
        

# parse_fights ()