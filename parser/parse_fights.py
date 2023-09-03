import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint

EVENTS_URL = "https://ufc.ru/events"
FIGHTERS_DF = pd.read_csv("data/fighters.csv", index_col=[0])
FIGHTERS_DATA_DF = pd.read_csv("data/fighters_data.csv", index_col=[0])

def parse_fights ():
    ...

parse_fights ()