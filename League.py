#%%
from bs4 import BeautifulSoup as bs
from bs4 import Comment
import requests
import pandas as pd
import datetime as dt

current_year = dt.datetime.strftime(dt.datetime.today(),'%Y')

class LeagueStats:
    def __init__(self,year=current_year):
        self.year = year


## league standings page (same page but for 2020 --> https://www.baseball-reference.com/leagues/majors/2020-standings.shtml)
standings = 'https://www.baseball-reference.com/leagues/MLB-standings.shtml'

## batting and pitching page (same page but for 2020 --> https://www.baseball-reference.com/leagues/majors/2020.shtml)
bat_pitch = 'https://www.baseball-reference.com/leagues/majors/2021.shtml'




# %%
