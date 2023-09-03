import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint
import time

MAIN_URL = "https://ufc.ru"
RATING_URL = "https://ufc.ru/rankings"

def parse_fighters ():
    response = requests.get(RATING_URL)
    soup = BeautifulSoup(response.text, "html.parser").find_all(name="div", attrs={"class": "view-grouping-content"})

    fighters = []

    # два цикла нужны потому что на сайте чемпионы по весовым категориям и полу представлены отдельно, а все остальные бойцы в табличном виде

    # цикл для забора информации по чемпионам
    for block in soup:
        fighter = {}

        try:
            # категория где фигурирует название Top Rank является абсолютной, а значит там смешаны все бойцы, что плохо, тк программа их разделяет по весовым категориям и по полу
            division = block.find(name="h4").get_text()
            if division.find("Top Rank") != -1: continue
            
            fighter["Division"] = division
            fighter["FighterID"] = randint(100000, 999999)
            # последний символ при заборе имени - пробел, поэтому он не берется
            fighter["Name"] = block.find(name="h5").get_text()[:-1]
            fighter["Rank"] = 0
            fighter["URL"] = MAIN_URL + block.find(name="h5").findChild(name="a").get("href")        
        
            fighters.append(fighter)
        except: continue

    # цикл для забора информации по остальным бойцам
    for content in soup:
        
        # категория где фигурирует название Top Rank является абсолютной, а значит там смешаны все бойцы, что плохо, тк программа их разделяет по весовым категориям и по полу
        division = content.find(name="h4").get_text()
        if division.find("Top Rank") != -1: continue   

        for block in content.findAll(name="tr"):
            fighter = {}

            fighter["Division"] = division
            fighter["FighterID"] = randint(100000, 999999)
            # последний символ при заборе имени - пробел, поэтому он не берется
            fighter["Name"] = block.find(name="td", attrs={"class": "views-field-title"}).get_text()[:-1]
            fighter["Rank"] = block.find(name="td", attrs={"class": "views-field-weight-class-rank"}).get_text().rstrip()
            fighter["URL"] = MAIN_URL + block.find(name="td", attrs={"class": "views-field-title"}).findChild(name="a").get("href")        
        
            fighters.append(fighter)


    fighters_df = pd.DataFrame(data=fighters)
    fighters_df.to_csv("data/fighters.csv")

# код парсинга данных бойца вынесен в отдельную функцию для более удобного использования
def parse_one_fighter (url: str, soup: BeautifulSoup) -> dict:
    fighter_data = {}
    
    try:
        # сбор физических показателей
        rows = soup.find_all(name="div", attrs={"class": "c-bio__row--3col"})
        # на сайте 2 div с  классами c-bio__row--3col
        row_0 = rows[0].find_all(name="div", attrs={"class": "c-bio__text"})
        fighter_data["Age"] = int(row_0[0].get_text())
        fighter_data["Height"] = float(row_0[1].get_text())
        fighter_data["Weight"] = float(row_0[2].get_text())

        row_1 = rows[1].find_all(name="div", attrs={"class": "c-bio__text"})
        # на сайте год первого боя в октагоне пишется в формате ГГ, поэтому int(f"20...") дописывает 20 к нему при парсинге. 
        # далее из текущего года вычитается год первого боя у бойца
        fighter_data["Experience"] = time.localtime()[0] - int(f"20{row_1[0].get_text().split('.')[2]}")
        fighter_data["Arm span"] = float(row_1[1].get_text())
        fighter_data["Leg span"] = float(row_1[2].get_text())
        # сбор показателей статистики ( точность ударов и т.д )
    
        # сбор точности ударов 
        # один тэг содержит информацию про точность ударов, другой - про точность тейкдаунов
        accuracy_strikes = soup.find(name="text", attrs={"class": "e-chart-circle__percent"})
        fighter_data["Accuracy strikes"] = int(accuracy_strikes.get_text().replace("%", ""))
        
        # сбор количества акц. ударов/мин., пропущ.акц. ударов/мин. , кол-во тейкдаунов/15 мин , процент защиты от акц.ударов/тейкдаунов
        # 8 тэгов содержат всю информацию, а нужную - теги под номером в массиве 0,1,2,4,5
        stat_strikes = soup.find_all(name="div", attrs={"class": "c-stat-compare__number"})
        fighter_data["Accented strikes"] = float(stat_strikes[0].get_text())
        fighter_data["Missed strikes"] = float(stat_strikes[1].get_text())
        fighter_data["Number takedowns"] = float(stat_strikes[2].get_text())
        fighter_data["Strike protection"] = int(stat_strikes[4].get_text().replace("%", ""))
        fighter_data["Takedown protection"] = int(stat_strikes[5].get_text().replace("%", ""))

        # изначально статистика представлена так: 26-5-0(В-П-Н) , поэтому необходимо выполнять много преобразований
        WLD_stat = soup.find(name="p", attrs={"class": "hero-profile__division-body"}).get_text().split("(")[0].split("-")
        fighter_data["Wins"] = int(WLD_stat[0])
        fighter_data["Losses"] = int(WLD_stat[1])
        fighter_data["Drafts"] = int(WLD_stat[2])

        # количество побед нокаутами ( на сайте 6 div с классом c-stat-3bar__value, кол-во побед КО/ТКО - div с порядковым номером в массиве 3)
        fighter_data["KO/TKO"] = int(soup.find_all(name="div", attrs={"class": "c-stat-3bar__value"})[3].get_text().split(" ")[0])
        
        return fighter_data
    except: 
        print(f"{url} - боец пропущен")
        return {}

def parse_fighters_data ():
    fighters_df = pd.read_csv("data/fighters.csv", usecols=["FighterID", "URL"])
    fighters_data = []

    
    for url in fighters_df["URL"]:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        fighter_data = parse_one_fighter(url, soup)
        if fighter_data == {}: continue
        fighters_data.append(fighter_data)


    fighters_columns = list(fighters_df.columns)
    fighters_columns.remove("URL")

    columns = fighters_columns + list(fighters_data[0].keys())
    fighters_data_df = pd.DataFrame(columns=columns)

    fighters_data_df = pd.concat([fighters_df["FighterID"], pd.DataFrame(fighters_data)], axis=1)
    fighters_data_df.dropna(inplace=True)
    
    fighters_data_df.to_csv("data/fighters_data.csv")