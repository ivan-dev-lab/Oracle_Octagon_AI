import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint
import logging
from parse_fighters import parse_fighter

MAIN_URL = "https://ufc.ru"
EVENTS_URL = "https://ufc.ru/events"

logging.basicConfig(level=logging.INFO, 
                    filename="logs/parser.log", 
                    filemode="w", 
                    format="%(asctime)s %(levelname)s %(message)s",
                    encoding="utf8")

logging.getLogger(__name__)

# на сайте представлена такая структура: 1 event = ссылка на чемпионат с множеством боев, поэтому парсятся сначала event
def parse_events () -> list:
    response = requests.get(EVENTS_URL+"#events-list-past")
    if response.status_code == 200: logging.info(msg=f"Подключение к {EVENTS_URL+'#events-list-past'} выполнено успешно")
    else: logging.warning(msg=f"Подключение к {EVENTS_URL+'#events-list-past'} не удалось. Код ошибки: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    Urls = []

    logging.info(msg="Начат процесс сбора чемпионатов/турниров")
    # на странице с ?page>=36 чемпионаты/турниры с теми бойцами, которые уже давно не выступают
    for i in range(55+1):
        current_response = requests.get(f"{EVENTS_URL}?page={i}#events-list-past")
        soup = BeautifulSoup(current_response.text, "html.parser")

        buttons = soup.find_all(name="a", attrs={"class": "e-button--white"})
        for link in buttons:
            if link.findNext("span").get_text().strip().lower() == "итоги":
                Urls.append(MAIN_URL+link.get("href"))   
    logging.info(msg="Процесс сбора чемпионатов/турниров успешно завершен")
    return Urls

def check_fighters (fighters_df: pd.DataFrame, names: list[str], urls: list[str]) -> tuple[list, list]:
    # В ID_list добавляются идентификаторы бойцов, которые нашлись в базе
    # В URL_list добавляются ссылки на тех бойцов, которых в базе нет
    # ссылки из URL_list будут парситься отдельно функцией parse_one_fighter() из parse_fighters.py
    # возвращает кортеж с массивами идентификаторов бойцов и ссылок на тех, кого надо парсить
    ID_list = []
    URL_list = []

    logging.info(msg=f"Идет проверка бойцов {urls[0]} и {urls[1]}")
    for index, name in enumerate(names):
        FighterID = fighters_df[fighters_df["Name"] == name]["FighterID"].values
    
        if FighterID.size > 0:             
            ID_list.append(FighterID[0])

        else: URL_list.append(urls[index])
    logging.info(msg=f"Проверка успешно завершена")

    return (ID_list, URL_list)

# тк при занесении новых бойцов ( один из результатов parse_fights () ) отсутсвуют такие данные, как имя и дивизион
# то эта функция будет парсить их отдельно
def get_fighter_bio (url: str) -> dict:
    response = requests.get(url)
    if response.status_code == 200: logging.info(msg=f"Подключение к {url} выполнено успешно")
    else: logging.warning(msg=f"Подключение к {url} не удалось. Код ошибки: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    bio = {}

    logging.info(msg=f"Идет сбор личных данных о бойце {url}")
    try:
        division = soup.find(name="p", attrs={"class": "hero-profile__tag"}).get_text().strip().replace("\n", "")
        if division.find("#") != -1: division = " ".join(division.split(" ")[1:]).strip()
            
        bio["Division"] = division
        bio["FighterID"] = randint(100000,999999)
        bio["Name"] = soup.find(name="h1", attrs={"class": "hero-profile__name"}).get_text()
        bio["URL"] = url
        logging.info(msg=f"Сбор данных успешно завершен")
        return bio
    except: 
        logging.info(msg=f"У бойца отсутствуют личные данные")
        return {}

def parse_fights () -> list():
    LINKS_EVENTS = parse_events()  
    result = [] # массив для возврата бойцов, которых добавили в базу и истории боёв
    fighters_df = pd.read_csv("data/fighters.csv", index_col=[0])
    fighters = []
    fight_cards = []

    for event_url in LINKS_EVENTS:
        logging.info(msg=f"Идет обработка чемпионата - {event_url}")
        response = requests.get(event_url)
        if response.status_code == 200: logging.info(msg=f"Подключение к {event_url} выполнено успешно")
        else: logging.warning(msg=f"Подключение к {url} не удалось. Код ошибки: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        fight_cards_ResultSet = soup.find(name="ul", attrs={"class": "l-listing__group--bordered"}).find_all(name="li")

        for i, card in enumerate(fight_cards_ResultSet):
            fight_card = {
                "FightID": randint(100000,999999),
                "URL": event_url 
            }
            # в данном случае card - карточка 1 боя

            # парсинг имён двух бойцов. Далее по ним ведется поиск в fighters.csv 
            # -> если находится - возвращает FighterID
            # -> если не находится, то пытается спарсить данные бойца. 
            # Если получается -> заносит бойца в fighters.csv и fighters_data.csv -> возвращает FighterID            
            fighter_names = []
            fighter_names.append(soup.find_all(name="div", attrs={"class": "c-listing-fight__corner-name--red"})[i].get_text().strip().replace("\n", " "))
            fighter_names.append(soup.find_all(name="div", attrs={"class": "c-listing-fight__corner-name--blue"})[i].get_text().strip().replace("\n", " "))

            fighter_urls = []
            fighter_urls.append(soup.find_all(name="div", attrs={"class": "c-listing-fight__corner-name--red"})[i].find(name="a").get("href"))
            fighter_urls.append(soup.find_all(name="div", attrs={"class": "c-listing-fight__corner-name--blue"})[i].find(name="a").get("href"))
            
            check_result = check_fighters(fighters_df, fighter_names, fighter_urls)
            
            # если в массиве с именами бойцов в бою 2 FighterID -> все бойцы найдены в базе
            if len(check_result[0]) == 2: 
                fight_card["FighterID_1"] = check_result[0][0]
                fight_card["FighterID_2"] = check_result[0][1]
            else:
                # если нет, то проверяется сначала хотя бы один FighterID -> с помощью которого ищется ссылка на него, 
                # а потом парсятся все ссылки из второго массива
                # это сделано с той целью, чтобы не потерять изначальный порядок бойцов. 
                # Пример: было: ([882259], ["https://ufc.ru/athlete/rayan-spenn"], 
                # стало: ["https://ufc.ru/athlete/volkan-ozdemir", "https://ufc.ru/athlete/rayan-spenn"])
                if len(check_result[0]) == 1:
                    url = fighters_df[fighters_df["FighterID"] == check_result[0][0]]["URL"].values[0]
                    check_result[0].clear()
                    check_result[1].append(url)
                    check_result[1].reverse() # reverse для того, чтобы сохранился порядок бойцов
                # порядок бойцов нужен для того, чтобы в столбцах Result_1 и Result_2 писался исход боя для каждого
                
                
                for i,url in enumerate(check_result[1], start=1):
                    if fighters_df[fighters_df["URL"] == url].values.size > 0:
                        fight_card[f"FighterID_{i}"] = fighters_df[fighters_df["URL"] == url]["FighterID"].values
                        continue
                    
                    fighter_bio = get_fighter_bio(url)
                    if fighter_bio == {}: 
                        fight_card.clear()
                        continue
                    
                    fighter = get_fighter_bio(url)
                    
                    fighter_data = parse_fighter(url)
                    if fighter_data == {}: 
                        fight_card.clear()
                        continue

                    fighter.update(fighter_data)
                    fight_card[f"FighterID_{i}"] = fighter["FighterID"]

                    fighters.append(fighter)
                
            fight_card[f"Result_1"] = card.find(name="div", attrs={"class": "c-listing-fight__corner-body--red"}).get_text().strip().replace("\n", " ")
            fight_card[f"Result_2"] = card.find(name="div", attrs={"class": "c-listing-fight__corner-body--blue"}).get_text().strip().replace("\n", " ")
            
            if len(fight_card) == 6:
                # именно 6, потому что карточка боя с 6 параметрами включает в себя: FightID, URL, 
                # FighterID_1, FighterID_2, Result_1, Result_2
                fight_cards.append(fight_card)

        logging.info(msg=f"Обработка чемпионата завершена успешно")
    
    result.append(pd.concat([fighters_df, pd.DataFrame(data=fighters)], ignore_index=True))        
    result.append(pd.DataFrame(data=fight_cards))
    return result