import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint
from parse_fighters import parse_fighter

MAIN_URL = "https://ufc.ru"
EVENTS_URL = "https://ufc.ru/events"

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

def check_fighters (fighters_df: pd.DataFrame, names: list[str], urls: list[str]) -> tuple[list, list]:
    # В ID_list добавляются идентификаторы бойцов, которые нашлись в базе
    # В URL_list добавляются ссылки на тех бойцов, которых в базе нет
    # ссылки из URL_list будут парситься отдельно функцией parse_one_fighter() из parse_fighters.py
    # возвращает кортеж с массивами идентификаторов бойцов и ссылок на тех, кого надо парсить
    ID_list = []
    URL_list = []

    for index, name in enumerate(names):
        FighterID = fighters_df[fighters_df["Name"] == name]["FighterID"].values
    
        if FighterID.size > 0:             
            ID_list.append(FighterID[0])

        else: URL_list.append(urls[index])

    return (ID_list, URL_list)

# тк при занесении новых бойцов ( один из результатов parse_fights () ) отсутсвуют такие данные, как имя и дивизион
# то эта функция будет парсить их отдельно
def get_fighter_bio (url: str) -> dict:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    bio = {}

    try:
        division = soup.find(name="p", attrs={"class": "hero-profile__tag"}).get_text().strip().replace("\n", "")
        if division.find("#") != -1: division = " ".join(division.split(" ")[1:]).strip()
            
        bio["Division"] = division
        bio["FighterID"] = randint(100000,999999)
        bio["Name"] = soup.find(name="h1", attrs={"class": "hero-profile__name"}).get_text()
        bio["URL"] = url

        return bio
    except: return {}


def parse_fights () -> list():
    LINKS_EVENTS = [] # parse_events()  
    # убрать после завершения работы    
    with open("events.txt", "r", encoding="utf8") as f:
        for line in f.readlines():
            LINKS_EVENTS.append(line.strip())
    result = [] # массив для возврата бойцов, которых добавили в базу и истории боёв
    fighters_df = pd.read_csv("data/fighters.csv", index_col=[0])
    fighters = []
    fight_cards = []
    for index,event_url in enumerate(LINKS_EVENTS):
        print(f"{index}/{len(LINKS_EVENTS)}")
        response = requests.get(event_url)
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
                        # print(f"{url} - боец уже есть в базе")
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
    
    result.append(pd.concat([fighters_df, pd.DataFrame(data=fighters)], ignore_index=True))        
    result.append(pd.DataFrame(data=fight_cards))
    return result