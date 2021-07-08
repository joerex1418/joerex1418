#%%
from bs4 import BeautifulSoup as bs
from bs4 import Comment
import requests
import pandas as pd
import datetime as dt

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time



class CompletedDay:
    """
    # Methods
    #### boxscores()
    --> returns a dictionary of all the boxscores for a specified day. (default 'date' is one day before the current)
    #### gameurl()
    --> returns URL of a specific game from user's query by team
    #### minibox()
    --> returns dictionary of a specific game's boxscore (uses the 'gameurl()' method to retrieve necessary URL)
    #### fullgame()
    --> possible to return dictionary of sub dicts or specific dataframe from sub dicts
        **see the method's documentation**
    
    """
    def __init__(self,date,boxes=[]):
        self.date = date
        self.boxes = boxes

    def __repr__(self):
        return ("Boxscores for ", self.date)

    def boxscores(self,date=None):
        self.date = date
        if date == None:
            url = 'https://www.baseball-reference.com/boxes/'
        else:
            url = 'https://www.baseball-reference.com/boxes/'+'?year='+date[0:4]+'&month='+date[5:7]+'&day='+date[-2:]

        req = requests.get(url)
        soup = bs(req.content,"html.parser")
        games = soup.find('div',class_="game_summaries")
        games_list = games.find_all(class_='game_summary nohover')

        bs_list = []

        for game in games_list:
            bs_dict = {}
            matchup = game.find_all('tbody')[0]
            pitchers = game.find_all('tbody')[1]

            bs_dict['away_team'] = matchup.find_all('tr')[0].find_all('td')[0].text
            bs_dict['away_score'] = matchup.find_all('tr')[0].find_all('td')[1].text
            bs_dict['away_url'] = matchup.find_all('tr')[0].find('a')['href']

            bs_dict['home_team'] = matchup.find_all('tr')[1].find_all('td')[0].text
            bs_dict['home_score'] = matchup.find_all('tr')[1].find_all('td')[1].text
            bs_dict['home_url'] = matchup.find_all('tr')[1].find('a')['href']

            if int(bs_dict['home_score']) > int(bs_dict['away_score']):
                bs_dict['home_result'] = 'W'
                bs_dict['away_result'] = 'L'
            else:
                bs_dict['home_result'] = 'L'
                bs_dict['away_result'] = 'W'

            pitch_results = pitchers.find_all('tr')

            if len(pitch_results) == 2:
                bs_dict['win_pitch'] = pitch_results[0].find_all('td')[1].text
                bs_dict['lose_pitch'] = pitch_results[1].find_all('td')[1].text

            else:
                bs_dict['win_pitch'] = pitch_results[0].find_all('td')[1].text
                bs_dict['lose_pitch'] = pitch_results[1].find_all('td')[1].text
                save_pitch = pitch_results[2].find_all('td')[1].text
            
            bs_dict['game_url'] = 'https://www.baseball-reference.com'+matchup.find('td',class_='right gamelink').find('a')['href']

            bs_list.append(bs_dict)

        self.boxes = bs_list

        return self.boxes

    def gameurl(self,date,query):
        boxscores_list = self.boxscores(date)
        for bs in boxscores_list:
            vals = [string.lower() for string in bs.values()]
            try:
                for val in vals:
                    if query.lower() in val:
                        return bs['game_url']
                    else:
                        pass
            except:
                print("No games were found for your search query")
                return "No url"
    
    def minibox(self,date,query):
        boxscores_list = self.boxscores(date)
        try:
            for idx,bs in enumerate(boxscores_list):
                vals = [string.lower() for string in bs.values()]
                for val in vals:
                    if query.lower() in val:
                        team_idx = idx
                        return boxscores_list[team_idx]
                    else:
                        pass
            
        except:
            print('No miniboxes found')
            return "No miniboxes found"

    def fullgame(self,query,date=None,returndf=None):
        """ 
        ## Parameters
        _____________________________________________
        #### *query* : typically a team name or part of a team name in order to find the specific game information
        #### *date* : date that the game took place. Should follow the 'yyyy-mm-dd' format (default is the date previously specified in the method's class attribute, 'self.date')
        #### *returndf* : optional; if specified, the method will return a single dictionary (depending on the dict selected - see available dicts below)
        If *returndf* parameter is not specified by user (default =None), the method will return a dictionary of all relevant game information stored in different individual dictionaries.
        If 'returndf' is specified, the method will return the specified dictionary as a dataframe.
        The user can enter in a specific dictionary (as a string) in the 'returndf' parameter to return it as a pandas DataFrame object


        ## Available dicts to return as DataFrames:
        =============================================
        ### 'info' 
        #### -> Displays miscellaneous game info such as the Date, Start Time, Attendance, etc.
        ### 'boxscore' 
        #### -> Displays the full box score grid with scoring for all innings
        ### 'awaybatting' 
        #### -> Displays away team's BATTING stats for the day
        ### 'homebatting' 
        #### -> Displays home team's BATTING stats for the day
        ### 'awaypitching' 
        #### -> Displays away team's PITCHING stats for the day
        ### 'homepitching' 
        #### -> Displays home team's PITCHING stats for the day

        ----
        If  'asDF' is 'False', user can get the headers formatted as a list for batting and pitching tables from 'game_dict'
        
        """
        if returndf == None:
            asDF = False
        else:
            asDF = True


        if date == None:
            date = self.date
        else:
            pass
        game_url = self.gameurl(date,query)
        req = requests.get(game_url)
        soup = bs(req.content,"html.parser")
        domain = 'https://www.baseball-reference.com'


        # info_dict = {} --> basic info for game (date, start time, attendance, venue, duration, etc.)

        info_dict = {}

        divs = soup.find('div',class_='scorebox_meta').find_all('div')[:-2]
        date_obj = dt.datetime.strptime(divs[0].text,'%A, %B %d, %Y')
        date_str = dt.datetime.strftime(date_obj, '%Y-%m-%d')
        try:
            info_dict['date'] = date_str
            info_dict['starttime'] = divs[1].text[12:]
            info_dict['attendance'] = divs[2].text[12:]
            info_dict['venue'] = divs[3].text[7:]
            info_dict['duration'] = divs[4].text[16:]
            try:
                info_dict['misc'] = divs[5].text
            except:
                info_dict['misc'] = 'n/a'
            info_dict['date_obj'] = date_obj
        except:
            pass



        # box_dict --> the full inning-by-inning scoreboard

        fullbox = soup.find('table',class_="linescore nohover stats_table no_freeze")
        thead = fullbox.find('thead').find_all('th')[2:]

        away = fullbox.find('tbody').find_all('tr')[0].find_all('td')[2:]
        home = fullbox.find('tbody').find_all('tr')[1].find_all('td')[2:]

        box_dict = {'away_team':fullbox.find('tbody').find_all('tr')[0].find_all('td')[1].text,
                    'away_link':domain+fullbox.find('tbody').find_all('tr')[0].find_all('td')[1].find('a')['href'],
                    'away_record':soup.find('div',class_='scorebox').find_all('div')[0].contents[4].text,
                    'home_team':fullbox.find('tbody').find_all('tr')[1].find_all('td')[1].text,
                    'home_link':domain+fullbox.find('tbody').find_all('tr')[1].find_all('td')[1].find('a')['href'],
                    'home_record':soup.find('div',class_='scorebox').contents[3].contents[4].text
                    }
        headings = []
        total_inns = len(thead)-3

        for idx, th in enumerate(thead):
            box_dict['away_'+th.text] = th.text
            box_dict['home_'+th.text] = th.text
            headings.append(th.text)

        for idx, td in enumerate(away):
            box_dict['away_'+str(headings[idx])] = td.text
        for idx, td in enumerate(home):
            box_dict['home_'+str(headings[idx])] = td.text

        box_dict['num_innings'] = str(total_inns)

        '''The rest of the tables are stored in the comments of the html. The next block of code singles that section out first so we are able to scrape through them.'''

        bcomments = soup.find_all(text=lambda text:isinstance(text,Comment)) # comments identified
        batting_comments = [] # a list store the necessary comment html for the BATTING tables
        for c in bcomments: # looks for only the necessary comment blocks for the last few tables
            if '<div class="table_container" id="div_' in c:
                batsoup = bs(str(c),'html.parser')
                batting_comments.append(batsoup)
            else:
                pass




        # away_bat_dict = {} --> batting stats for away team
            
        abat_dict = {}
        abat_soup = batting_comments[0]
        ab_headers = abat_soup.find('thead').find_all('th')[1:14]
        ab_head_list = []

        for th in ab_headers:
            ab_head_list.append(th.text)

        ab_data = abat_soup.find('tbody').find_all('tr')
        for idx,row in enumerate(ab_data):
            try:
                indiv_stats = []
                player = row.find('th').find('a').text
                for td in row.find_all('td')[0:13]:
                    indiv_stats.append(td.text.strip())
                
                indiv_stats.append(player)

                abat_dict[player] = indiv_stats # 'abat_dict' is essentially just a dictionary of stats for a specific player
                abat_dict[str(idx+1)] = indiv_stats ## (^^same with 'hbat_dict' in the next block of code)
            except:
                pass


        # hbat_dict = {} --> batting stats for home team

        hbat_dict = {}
        hbat_soup = batting_comments[1]
        hb_headers = hbat_soup.find('thead').find_all('th')[1:14]
        hb_head_list = []

        for th in hb_headers:
            hb_head_list.append(th.text)

        hb_data = hbat_soup.find('tbody').find_all('tr')
        for idx,row in enumerate(hb_data):
            try:
                indiv_stats = []
                player = row.find('th').find('a').text

                for td in row.find_all('td')[0:13]:
                    indiv_stats.append(td.text.strip())
                
                indiv_stats.append(player)

                hbat_dict[player] = indiv_stats
                hbat_dict[str(idx+1)] = indiv_stats
            except:
                pass

        #######  creates standard list called 'batting_headers'. 
        #######  It is the same as 'ab_head_list' and 'hb_head_list'
        batting_headers = hb_head_list
        ####################################
        away_ref = box_dict['away_team'].replace(" ","")+'pitching' # used to search for the away team's pitching table in the comments
        home_ref = box_dict['home_team'].replace(" ","")+'pitching' # used to search for the home team's pitching table in the comments
    
        '''Similar process as above but for the comments that include PITCHING stat tables'''
        # print(str(box_dict['away_team']).strip(' ')+'pitching')
        # print(str(box_dict['home_team']).strip(' ')+'pitching')
        pcomments = soup.find_all(text=lambda text:isinstance(text,Comment)) # comments identified
        pitching_comments = [] # a list store the necessary comment html for the PITCHING tables

        for c in pcomments: # looks for only the necessary comment blocks for the last few tables
            if away_ref in c:
                pitchsoup = bs(str(c),'html.parser')
                pitching_comments.append(pitchsoup)
            elif home_ref in c:
                pitchsoup = bs(str(c),'html.parser')
                pitching_comments.append(pitchsoup)
            else:
                pass

        
        # apit_dict = {} --> pitching stats for away team

        apit_dict = {}
        apit_soup = pitching_comments[0]
        ap_headers = apit_soup.find('thead').find_all('th')[1:19]
        ap_head_list = []

        for th in ap_headers:
            ap_head_list.append(th.text)
        ap_data = apit_soup.find('tbody').find_all('tr')
        for idx,row in enumerate(ap_data):
            try:
                pitch_stats = []
                player = row.find('th').find('a').text
                for td in row.find_all('td')[:18]:
                    pitch_stats.append(td.text.strip())

                pitch_stats.append(player)

                apit_dict[player] = pitch_stats
                apit_dict[str(idx+1)] = pitch_stats
            except:
                pass

        # hpit_dict = {} --> pitching stats for home team

        hpit_dict = {}
        hpit_soup = pitching_comments[0]
        hp_headers = hpit_soup.find('thead').findNext('thead').find_all('th')[1:19]
        hp_head_list = []

        for th in hp_headers:
            hp_head_list.append(th.text)
        pitching_headers = hp_head_list
        hp_data = hpit_soup.find('tbody').findNext('tbody').find_all('tr')
        for idx,row in enumerate(hp_data):
            try:
                pitch_stats = []
                player = row.find('th').find('a').text
                for td in row.find_all('td')[:18]:
                    pitch_stats.append(td.text.strip())

                pitch_stats.append(player)

                hpit_dict[player] = pitch_stats
                hpit_dict[str(idx+1)] = pitch_stats
            except:
                pass


        # game_dict = {} --> dictionary of ALL dictionaries
        possible_dicts = ['boxscore','awaybatting','homebatting','awaypitching','homepitching']
        if asDF == False:
            game_dict = {'info':info_dict,
                    'boxscore':box_dict,
                    'awaybatting':abat_dict,
                    'homebatting':hbat_dict,
                    'awaypitching':apit_dict,
                    'homepitching':hpit_dict,
                    'batheaders':batting_headers,
                    'pitchheaders':pitching_headers}
            return game_dict
        else:
            if returndf in possible_dicts:
                if returndf == 'boxscore':
                    num_innings = int(box_dict['num_innings'])
                    unwanted_keys = ['away_team','home_team','away_link','home_link','away_record','home_record','num_innings']

                    heading = []
                    for i in range(num_innings):
                        heading.append(str(i+1))
                    heading.append('R')
                    heading.append('H')
                    heading.append('E')

                    away_data = []
                    home_data = []
                    for key,val in box_dict.items():
                        if key not in unwanted_keys:
                            if 'away' in key:
                                away_data.append(val)
                            else:
                                home_data.append(val)
                        else:
                            pass
                    df = pd.DataFrame.from_dict(data={box_dict['away_team']:away_data,box_dict['home_team']:home_data}, orient='index',columns=heading)
                    return df

                elif returndf == 'awaybatting':
                    df_dict = {}
                    for key,val in abat_dict.items():
                        if ' ' not in key:
                            pass
                        else:
                            df_dict[key] = val[:-1]
                    df = pd.DataFrame.from_dict(data=df_dict,orient='index',columns=batting_headers)
                    df = df.replace('',value='--')
                    return df

                elif returndf == 'homebatting':
                    df_dict = {}
                    for key,val in hbat_dict.items():
                        if ' ' not in key:
                            pass
                        else:
                            df_dict[key] = val[:-1]
                    df = pd.DataFrame.from_dict(data=df_dict,orient='index',columns=batting_headers)
                    df = df.replace('',value='--')
                    return df

                elif returndf == 'awaypitching':
                    df_dict = {}
                    for key,val in apit_dict.items():
                        if ' ' not in key:
                            pass
                        else:
                            df_dict[key] = val[:-1]
                    df = pd.DataFrame.from_dict(data=df_dict,orient='index',columns=pitching_headers)
                    df = df.replace('',value='--')
                    return df

                else: # (returndf == 'homepitching')
                    df_dict = {}
                    for key,val in hpit_dict.items():
                        if ' ' not in key:
                            pass
                        else:
                            df_dict[key] = val[:-1]
                    df = pd.DataFrame.from_dict(data=df_dict,orient='index',columns=pitching_headers)
                    df = df.replace('',value='--')
                    return df
            else:
                print("ERROR: Must assign one of the following to the 'returndf' parameter:\n('boxscore','awaybatting','homebatting','awaypitching','homepitching')")






#%%

user_date = dt.datetime.today() - dt.timedelta(days=1)
user_date = dt.datetime.strftime(user_date,'%Y-%m-%d')

print(user_date)
day1 = CompletedDay(user_date)
# box_scores = day1.boxscores(user_date)
# url = day1.gameurl(user_date,'white sox')
# sox_mini = day1.minibox(user_date,'white sox')
# sox_full = day1.fullgame('white sox')
gameinfo = day1.fullgame('pirates')

pd.DataFrame.from_dict(gameinfo)

















####################### GOTTA FIX ISSUE WITH OLDER GAMES --- SOME DON'T HAVE THE 'Pit' and 'Str' stat
#######################








# %%
