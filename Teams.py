#%%
from bs4 import BeautifulSoup as bs
from bs4 import Comment
import lxml
from bs4.builder import HTML_5
import requests
import pandas as pd
import re
import datetime as dt
from unidecode import unidecode as uc

#%%

class Teams:
    def __init__(self):
        teamsurl = 'https://www.baseball-reference.com/teams/'
        req = requests.get(teamsurl)
        soup = bs(req.content,'lxml')
        franch_soup = soup.find('caption',text='Active Franchises').findNext('tbody').findAll('td',attrs={'data-stat':'franchise_name'})
        teams_dict = {}
        for team in franch_soup:
            teams_dict[team.text] = 'https://www.baseball-reference.com'+str(team.find('a')["href"])
        self.directory = teams_dict
    
    def geturl(self,query=None):
        directory = self.directory
        for key,val in directory.items():
            if query.lower() in key.lower():
                url = val
                return url
            else:
                pass

    def teaminfo(self,query=None):
        """
        ## given a search query (must be a team name or part of team name), will return a dictionary of basic team info
        ____________________________________________________________________________
        ### dictionary keys are 'Team Names'(or 'Team Name'), 'Seasons', 'Record', 'Playoff Appearances', 'Pennants', 'World Championships', and 'Top Manager' 
        ### (not case-sensitive)"""
        if query == None:
            print('MUST INCLUDE TEAM SEARCH QUERY (type:str) (E.g. - "White Sox", "cubs", "diamondbacks","Boston"')
        else:
            url = self.geturl(query)
            req = requests.get(url)
            soup = bs(req.content,'lxml')
            infosoup = soup.find('h1',attrs={'itemprop':'name'}).findParent('div')
            summary_dict = {}
            for ptag in infosoup.findAll('p'):
                if 'also played as' in ptag.text.lower():
                    pass
                else:
                    label = ptag.find('strong').text
                    txt = ptag.text[ptag.text.find(':')+1:]
                    txt = txt.replace('\n',' ')
                    txt = txt.strip(' ')
                    if 'manager' in label.lower():
                        summary_dict['Top Manager'] = txt
                        summary_dict['top manager'] = txt
                    elif 'team name' in label.lower():
                        summary_dict['Team Names'] = txt
                        summary_dict['team names'] = txt
                        summary_dict['Team Name'] = txt
                        summary_dict['team name'] = txt
                    else:
                        summary_dict[label[:-1]] = txt
                        summary_dict[label[:-1].lower()] = txt
            return summary_dict
    
    def franchise(self,query=None,returndf=True):
        url = self.geturl(query)
        req = requests.get(url)
        soup = bs(req.content,'lxml').find('caption',text = 'Franchise History').findParent('table')
        thead = soup.find('thead').findAll('th')[1:]
        tbody = soup.find('tbody').findAll('tr')
        headings = []
        franchise_dict = {}
        for th in thead:
            headings.append(th.text)
        for tr in tbody:
            label = tr.find('th').text
            row_data = []
            for td in tr.findAll('td'):
                if td['data-stat'] == 'managers':
                    row_data.append(td.find('a')['title'])
                elif td['data-stat'] == 'war_leader':
                    row_data.append(td.find('a')['title'])
                else:
                    txt = td.text.replace('\xa0',' ')
                    row_data.append(txt)
            franchise_dict[label] = row_data
        

        if returndf == True:
            return pd.DataFrame.from_dict(franchise_dict,orient='index',columns=headings)
        else: return franchise_dict

    def yearstats(self,query=None,returndf=True,year=str(dt.date.today().year)):
        url = self.geturl(query) + year + '.shtml'
        req = requests.get(url)
        soup = bs(req.content,'lxml').find('caption',text='Team Batting').findParent('table')
        thead = soup.find('thead').findAll('th')
        tbody = soup.find('tbody').findAll('tr')
        headings = []
        teamstats_dict = {}
        for th in thead[1:]:
            headings.append(th.text)
        
        for tr in tbody:
            tds = tr.findAll('td')
            row_data = []
            try:
                pname = tr.find('td',attrs={'data-stat':'player'}).find('a').text
                for td in tds:
                    if td['data-stat'] == 'player':
                        row_data.append(td.find('a').text)
                    else:
                        row_data.append(td.text)
                teamstats_dict[pname] = row_data
            except:
                pass
        if returndf == True:
            return pd.DataFrame.from_dict(teamstats_dict,orient='index',columns=headings)
        else:
            return teamstats_dict




teams = Teams()
teams.yearstats('white sox',year='2021')


# %%

from Players import Players
abreu = Players.playerinfo


# %%
