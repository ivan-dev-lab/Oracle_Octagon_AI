import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint

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
            fighter["Name"] = block.find(name="h5").get_text()
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
            fighter["Name"] = block.find(name="td", attrs={"class": "views-field-title"}).get_text()
            fighter["Rank"] = block.find(name="td", attrs={"class": "views-field-weight-class-rank"}).get_text().rstrip()
            fighter["URL"] = MAIN_URL + block.find(name="td", attrs={"class": "views-field-title"}).findChild(name="a").get("href")        
        
            fighters.append(fighter)


    fighters_df = pd.DataFrame(data=fighters)
    fighters_df.to_csv("data/fighters.csv")