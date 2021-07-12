#%%
from logging import getLevelName
from platform import win32_edition
from bs4 import BeautifulSoup as bs, element
from bs4 import Comment
from numpy import kaiser, record

import requests
import pandas as pd
import datetime as dt

from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from sys import platform
if platform == 'darwin':
    useros = 'mac'
    driverloc = "/Applications/chromedriver"
    phantjs = "/Applications/phantomjs-2.1.1-macosx/bin/phantomjs"
elif platform == 'win32':
    useros = 'windows'
    driverloc = "C:\Program Files\chromedriver\chromedriver.exe"
    phantjs = "C:\Program Files\PhantomJS\phantomjs-2.1.1-windows\exe\phantomjs.exe"
elif platform == 'linux' or platform == 'linux2':
    useros = 'linux'
else:
    useros = 'idk'
todayobj = dt.datetime.today()
yestobj = todayobj - dt.timedelta(days=1)
today = dt.datetime.strftime(todayobj,'%Y-%m-%d')
yesterday = dt.datetime.strftime(yestobj,'%Y-%m-%d')


#%%
class Scores:
    def __init__(self,dateinput=dt.datetime.strftime(dt.datetime.today(),'%Y-%m-%d')):
        self.dateinput = dateinput

    def Previews(self,datein = None):
        if datein == None:
            datein = self.dateinput
            gamesurl = 'https://www.espn.com/mlb/scoreboard/_/date/'+datein
        else:
            gamesurl = 'https://www.espn.com/mlb/scoreboard/_/date/'+datein
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(executable_path=driverloc,options=options)
        driver.get(gamesurl)
        html = driver.execute_script("return document.getElementById('events').innerHTML")
        soup = bs(html,'lxml')
        allgames = soup.findAll('article')
        previews_dict = {}
        for box in allgames:
            preview_dict = {}
            gameid = box['id']
            status = box.find('tr',class_='sb-linescore').text.strip()
            preview_dict['GameID'] = gameid
            preview_dict['Status'] = status
            awayteam = box.find('td',class_='away').find('span',class_='sb-team-short').text
            awayrecord = box.find('td',class_='away').find('p',class_='record overall').text
            
            hometeam = box.find('td',class_='home').find('span',class_='sb-team-short').text
            homerecord = box.find('td',class_='home').find('p',class_='record overall').text
            
            preview_dict['AwayTeam'] = awayteam
            preview_dict['AwayTeamRecord'] = awayrecord
            preview_dict['HomeTeam'] = hometeam
            preview_dict['HomeTeamRecord'] = homerecord

            try:
                if 'postponed' in status.lower():
                    preview_dict['Status'] = 'Postponed'
                    venue = '--'
                    awaysp = '--'
                    homesp = '--'
                    
                    awpitchrec = '--'
                    awpitchera = '--'

                    hmpitchrec = '--'
                    hmpitchera = '--'
                    
                    preview_dict['Venue'] = venue
                    preview_dict['AwaySP'] = awaysp
                    preview_dict['HomeSP'] = homesp
                    preview_dict['AwayPitRec'] = awpitchrec
                    preview_dict['AwayPitERA'] = awpitchera
                    preview_dict['HomePitRec'] = hmpitchrec
                    preview_dict['HomePitERA'] = hmpitchera
                else:
                    status = box.find('span',class_='time').text
                    venue = box.find('section',class_='sb-detail').find('h6').text

                    awaysp = box.find('td',class_='away').find('div',class_='sb-meta pitchers').find('a').text
                    awpstats = box.find('td',class_='away').find('div',class_='sb-meta pitchers').find('p').text
                    awpitchrec = awpstats[1:awpstats.find(',')]
                    awpitchera = awpstats[awpstats.find(' ')+1:-1]

                    homesp = box.find('td',class_='home').find('div',class_='sb-meta pitchers').find('a').text
                    hmpstats = box.find('td',class_='home').find('div',class_='sb-meta pitchers').find('p').text
                    hmpitchrec = hmpstats[1:hmpstats.find(',')]
                    hmpitchera = hmpstats[hmpstats.find(' ')+1:-1]

                    preview_dict['Status'] = status
                    preview_dict['Venue'] = venue
                    preview_dict['AwaySP'] = awaysp
                    preview_dict['HomeSP'] = homesp
                    preview_dict['AwayPitRec'] = awpitchrec
                    preview_dict['AwayPitERA'] = awpitchera
                    preview_dict['HomePitRec'] = hmpitchrec
                    preview_dict['HomePitERA'] = hmpitchera
                


                previews_dict[awayteam+' at '+hometeam] = preview_dict

                
            except:
                pass
                
        return previews_dict

    def LiveGame(self,query='white sox'):
        try:
            try:
                gameid = self.liveurl(query)
            except:
                print('This team may not be playing right now. Try another query')
                return None
            gameurl = 'https://www.espn.com/mlb/boxscore/_/gameId/'+gameid
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--incognito')
            driver = webdriver.Chrome(executable_path=driverloc,options=options)
            driver.get(gameurl)
            time.sleep(1)
            # bannerhtml = driver.execute_script("return document.getElementById('gamepackage-matchup-wrap').innerHTML")
            # boxhtml = driver.execute_script("return document.getElementById('gamepackage-box-score').innerHTML")
            # linehtml = driver.execute_script("return document.getElementById('gamepackage-linescore').innerHTML")
            boxhtml = driver.page_source
            linehtml = driver.page_source
            bannerhtml = driver.page_source
            driver.quit()
            soupbox = bs(boxhtml,'lxml')
            soupline = bs(linehtml,'lxml')
            soupbanner = bs(bannerhtml,'lxml')
            gamedict = {}

            ############################################################################################
            # BOXSCORE # ---------------- ('boxscore' is referred to as 'linescore' on ESPN's HTML code)
            ############################################################################################
            ## find all data-athlete-id 's in soupbanner. If there are 3, then it is in "due up" mode)

            
            inn = soupbanner.find('span',class_='status-detail').text
            awayteam = soupbanner.find('div',class_='team away').find('span',class_='short-name').text
            hometeam = soupbanner.find('div',class_='team home').find('span',class_='short-name').text
            gamedict['Inning'] = inn
            gamedict['AwayTeam'] = awayteam
            gamedict['HomeTeam'] = hometeam
            
            table = soupline.find('table',class_='linescore__table')
            headers = table.find('thead').findAll('td')[1:]
            away = table.findAll('tbody')[0].findAll('td')[1:]
            home = table.findAll('tbody')[1].findAll('td')[1:]
            head = []
            for td in headers:
                head.append(td.text)
            awayrow = []
            for td in away:
                awayrow.append(td.text.strip())
            homerow = []
            for td in home:
                homerow.append(td.text.strip())
            gamedict['BoxLabels'] = head
            gamedict['AwayScoring'] = awayrow
            gamedict['HomeScoring'] = homerow
            
            if 'top' in inn.lower() or 'bottom' in inn.lower():
                try:
                    pitching = soupline.find('span',text='Pitcher').findNext('span',class_='fullName').text
                    atbat = soupline.find('span',text='Batter').findNext('span',class_='fullName').text
                    pitcherstats = soupline.find('span',text='Pitcher').findNext('span',class_='statline').text.strip()
                    gamedict['Pitching'] = pitching
                    gamedict['AtBat'] = atbat
                    gamedict['PitchStats'] = pitcherstats
                except:
                    pass
                ballorbs = soupline.find('ul',class_='count count--ball').findAll('li')
                ballct = 0
                for orb in ballorbs:
                    if ' '.join(orb['class']) == 'orb fill':
                        ballct+=1

                strikeorbs = soupline.find('ul',class_='count count--strike').findAll('li')
                strikect = 0
                for orb in strikeorbs:
                    if ' '.join(orb['class']) == 'orb fill':
                        strikect+=1

                outorbs = soupline.find('ul',class_='count count--out').findAll('li')
                outct = 0
                for orb in outorbs:
                    if ' '.join(orb['class']) == 'orb fill':
                        outct+=1
                diamonds = soupline.find('div',class_='situation__count').findNext('div')['class'][-1]
                first = diamonds[-5]
                second = diamonds[-3]
                third = diamonds[-1]
                
                gamedict['Balls'] = ballct
                gamedict['Strikes'] = strikect
                gamedict['Outs'] = outct
                gamedict['Bases'] = [first,second,third]
            else:
                try:
                    upnextname = soupline.findAll('div',class_='linescore__player')[0].find('span',class_='abbrName').text
                    upnextspot = soupline.findAll('div',class_='linescore__player')[0].find('span',class_='position').text
                    upnextstat = soupline.findAll('div',class_='linescore__player')[0].find('span',class_='statline').text
                    ondeckname = soupline.findAll('div',class_='linescore__player_stats')[1].find('span',class_='abbrName').text
                    ondeckspot = soupline.findAll('div',class_='linescore__player_stats')[1].find('span',class_='position').text
                    ondeckstat = soupline.findAll('div',class_='linescore__player_stats')[1].find('span',class_='statline').text
                    holename = soupline.findAll('div',class_='linescore__player_stats')[2].find('span',class_='abbrName').text
                    holespot = soupline.findAll('div',class_='linescore__player_stats')[2].find('span',class_='position').text
                    holestat = soupline.findAll('div',class_='linescore__player_stats')[2].find('span',class_='statline').text

                    upnext = [upnextname,upnextspot,upnextstat]
                    ondeck = [ondeckname,ondeckspot,ondeckstat]
                    hole = [holename,holespot,holestat]
                    
                    gamedict['DueUp'] = [upnext,ondeck,hole]
                except:
                    pass
            
            
            
            #######################################
            #  BATTING/PITCHING LINEUPS AND STATS #
            #######################################

            awaybatting = soupbox.findAll('table',attrs={'data-type':'batting'})[0].findAll('tbody')[:-1]
            homebatting = soupbox.findAll('table',attrs={'data-type':'batting'})[1].findAll('tbody')[:-1]
            abat_dict = {}
            for hitter in awaybatting:
                if ' '.join(hitter['class']) == 'athletes':
                    stats_dict = {}
                    ## TEST THE NEXT 4 LINES OF CODE TO MAKE SURE THEY WORK ##
                    plurl = hitter.find('td',class_='name').find('a')['href']
                    req = requests.get(plurl)
                    hname = bs(req.content,'lxml').find('title').text
                    hname = hname[:hname.find('Stats')].strip()

                    # name = hitter.find('td',class_='name').find('a').text           
                    stats_dict['Pos'] = hitter.find('td',class_='name').find('a').next_sibling
                    stats_dict['AB'] = hitter.find('td',class_='batting-stats-ab').text
                    stats_dict['R'] = hitter.find('td',class_='batting-stats-r').text
                    stats_dict['H'] = hitter.find('td',class_='batting-stats-h').text
                    stats_dict['RBI'] = hitter.find('td',class_='batting-stats-rbi').text
                    stats_dict['BB'] = hitter.find('td',class_='batting-stats-bb').text
                    stats_dict['K'] = hitter.find('td',class_='batting-stats-k').text
                    stats_dict['P'] = hitter.find('td',class_='batting-stats-p').text
                    stats_dict['AVG'] = hitter.find('td',class_='batting-stats-avg').text
                    stats_dict['OBP'] = hitter.find('td',class_='batting-stats-obp').text
                    stats_dict['SLG'] = hitter.find('td',class_='batting-stats-slg').text
                    abat_dict[hname] = stats_dict
                else:
                    stats_dict = {}
                    plurl = hitter.find('td',class_='name').find('a')['href']
                    req = requests.get(plurl)
                    hname = bs(req.content,'lxml').find('title').text
                    hname = hname[:hname.find('Stats')].strip()

                    # name = hitter.find('td',class_='name').find('a').text           
                    stats_dict['Pos'] = hitter.find('td',class_='name').find('a').next_sibling
                    stats_dict['AB'] = hitter.find('td',class_='batting-stats-ab').text
                    stats_dict['R'] = hitter.find('td',class_='batting-stats-r').text
                    stats_dict['H'] = hitter.find('td',class_='batting-stats-h').text
                    stats_dict['RBI'] = hitter.find('td',class_='batting-stats-rbi').text
                    stats_dict['BB'] = hitter.find('td',class_='batting-stats-bb').text
                    stats_dict['K'] = hitter.find('td',class_='batting-stats-k').text
                    stats_dict['P'] = hitter.find('td',class_='batting-stats-p').text
                    stats_dict['AVG'] = hitter.find('td',class_='batting-stats-avg').text
                    stats_dict['OBP'] = hitter.find('td',class_='batting-stats-obp').text
                    stats_dict['SLG'] = hitter.find('td',class_='batting-stats-slg').text
                    abat_dict[hname] = stats_dict
            hbat_dict = {}
            gamedict['AwayLineup'] = abat_dict
            for hitter in homebatting:
                if ' '.join(hitter['class']) == 'athletes':
                    stats_dict = {}
                    plurl = hitter.find('td',class_='name').find('a')['href']
                    req = requests.get(plurl)
                    hname = bs(req.content,'lxml').find('title').text
                    hname = hname[:hname.find('Stats')].strip()

                    # name = hitter.find('td',class_='name').find('a').text           
                    stats_dict['Pos'] = hitter.find('td',class_='name').find('a').next_sibling
                    stats_dict['AB'] = hitter.find('td',class_='batting-stats-ab').text
                    stats_dict['R'] = hitter.find('td',class_='batting-stats-r').text
                    stats_dict['H'] = hitter.find('td',class_='batting-stats-h').text
                    stats_dict['RBI'] = hitter.find('td',class_='batting-stats-rbi').text
                    stats_dict['BB'] = hitter.find('td',class_='batting-stats-bb').text
                    stats_dict['K'] = hitter.find('td',class_='batting-stats-k').text
                    stats_dict['P'] = hitter.find('td',class_='batting-stats-p').text
                    stats_dict['AVG'] = hitter.find('td',class_='batting-stats-avg').text
                    stats_dict['OBP'] = hitter.find('td',class_='batting-stats-obp').text
                    stats_dict['SLG'] = hitter.find('td',class_='batting-stats-slg').text
                    hbat_dict[hname] = stats_dict
                
                else:
                    stats_dict = {}
                    plurl = hitter.find('td',class_='name').find('a')['href']
                    req = requests.get(plurl)
                    hname = bs(req.content,'lxml').find('title').text
                    hname[:hname.find('Stats')].strip()

                    # name = hitter.find('td',class_='name').find('a').text+'-PH'           
                    stats_dict['Pos'] = hitter.find('td',class_='name').find('a').next_sibling
                    stats_dict['AB'] = hitter.find('td',class_='batting-stats-ab').text
                    stats_dict['R'] = hitter.find('td',class_='batting-stats-r').text
                    stats_dict['H'] = hitter.find('td',class_='batting-stats-h').text
                    stats_dict['RBI'] = hitter.find('td',class_='batting-stats-rbi').text
                    stats_dict['BB'] = hitter.find('td',class_='batting-stats-bb').text
                    stats_dict['K'] = hitter.find('td',class_='batting-stats-k').text
                    stats_dict['P'] = hitter.find('td',class_='batting-stats-p').text
                    stats_dict['AVG'] = hitter.find('td',class_='batting-stats-avg').text
                    stats_dict['OBP'] = hitter.find('td',class_='batting-stats-obp').text
                    stats_dict['SLG'] = hitter.find('td',class_='batting-stats-slg').text
                    hbat_dict[hname] = stats_dict
            gamedict['HomeLineup'] = hbat_dict



            awaypitching = soupbox.findAll('th',text='Pitchers')[0].findParent('table').findAll('tbody',class_='athletes')
            homepitching = soupbox.findAll('th',text='Pitchers')[1].findParent('table').findAll('tbody',class_='athletes')
            # ip, h, r, er, bb, k, hr, era
            apitch_dict = {}
            for pitcher in awaypitching:
                stats_dict = {}
                name = pitcher.find('td',class_='name').find('a').text
                name = name[:name.find('Stats')].strip()
                stats_dict['IP']= pitcher.find('td',class_='pitching-stats-ip').text
                stats_dict['H'] = pitcher.find('td',class_='pitching-stats-h').text
                stats_dict['R'] = pitcher.find('td',class_='pitching-stats-r').text
                stats_dict['ER'] = pitcher.find('td',class_='pitching-stats-er').text
                stats_dict['BB'] = pitcher.find('td',class_='pitching-stats-bb').text
                stats_dict['K'] = pitcher.find('td',class_='pitching-stats-k').text
                stats_dict['HR'] = pitcher.find('td',class_='pitching-stats-hr').text
                stats_dict['PC-ST'] = pitcher.find('td',class_='pitching-stats-pc-st').text
                stats_dict['ERA'] = pitcher.find('td',class_='pitching-stats-era').text
                stats_dict['PC'] = pitcher.find('td',class_='pitching-stats-pc').text
                apitch_dict[name] = stats_dict
            gamedict['AwayPitching'] = apitch_dict

            hpitch_dict = {}
            for pitcher in homepitching:
                stats_dict = {}
                name = pitcher.find('td',class_='name').find('a').text
                name = name[:name.find('Stats')].strip()
                stats_dict['IP']= pitcher.find('td',class_='pitching-stats-ip').text
                stats_dict['H'] = pitcher.find('td',class_='pitching-stats-h').text
                stats_dict['R'] = pitcher.find('td',class_='pitching-stats-r').text
                stats_dict['ER'] = pitcher.find('td',class_='pitching-stats-er').text
                stats_dict['BB'] = pitcher.find('td',class_='pitching-stats-bb').text
                stats_dict['K'] = pitcher.find('td',class_='pitching-stats-k').text
                stats_dict['HR'] = pitcher.find('td',class_='pitching-stats-hr').text
                stats_dict['PC-ST'] = pitcher.find('td',class_='pitching-stats-pc-st').text
                stats_dict['ERA'] = pitcher.find('td',class_='pitching-stats-era').text
                stats_dict['PC'] = pitcher.find('td',class_='pitching-stats-pc').text
                hpitch_dict[name] = stats_dict
            gamedict['HomePitching'] = hpitch_dict

            return gamedict
        except:
            try:
                pass
            except:
                pass
                print('ERROR in 1st Try Block')
                return None

    def Results(self,query=None,datein=today):
        datein = datein.replace('-','')
        gamelinks = self.geturls(datein=datein)
        if query == None:
            links = []
            for key,val in list(gamelinks.items()):
                if 'FINAL' in key:
                    links.append(val)
                else:
                    pass
            return links
        else:
            for key,val in list(gamelinks.items()):
                if query.lower() in key.lower():
                    link = val
        gameurl = link
        options = Options()
        options.headless = True
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        driver = webdriver.Chrome(executable_path=driverloc,options=options)
        driver.get(gameurl)
        html = driver.execute_script("return document.getElementById('gamepackage-box-score').innerHTML")
        # time.sleep(1)
        # html = driver.page_source
        driver.quit()
        sesh = requests.Session()
        req = sesh.get(gameurl)
        soup = bs(req.content,'lxml')
        linescore = soup.find('table',class_='linescore__table')
        headers = []
        awayrow = []
        homerow = []

        for td in linescore.find('thead').findAll('td')[1:]:
            headers.append(td.text.strip())
        for td in linescore.findAll('tbody')[0].findAll('td')[1:]:
            awayrow.append(td.text.strip())
        for td in linescore.findAll('tbody')[1].findAll('td')[1:]:
            homerow.append(td.text.strip())


        win = soup.find('span',text='WIN').findNext('span').find('span',class_='fullName').text
        loss = soup.find('span',text='LOSS').findNext('span').find('span',class_='fullName').text


        away = soup.find('div',class_='boxscore-2017__wrap boxscore-2017__wrap--away')
        awayteam = soup.find('div',class_='team away').find('span',class_='short-name').text
        awayhit = away.find('table',attrs={'data-type':'batting'}).findAll('tbody')[:-1]
        awaypit = away.find('table',attrs={'data-type':'pitching'}).findAll('tbody')[:-1]

        hitheaders = ['Pos']
        hithead = away.find('thead').findAll('th')[1:]
        for i in hithead:
            hitheaders.append(i.text)
        pitheaders = ['--']
        pithead = away.find('th',text='Pitchers').findParent('thead').findAll('th')[1:]
        for i in pithead:
            pitheaders.append(i.text)

        awayhitting = {}
        awaypitching = {}
        for tbody in awayhit:
            namelink = tbody.find('td',class_='name').find('a')['href']
            req = requests.get(namelink)
            soup = bs(req.content,'lxml')
            name = soup.find('title').text
            name = name[:name.find('Stats')].strip()
            stats = []
            stats.append(tbody.find('td',class_='name').find('a').next_sibling)
            for td in tbody.findAll('td')[1:]:
                stats.append(td.text)
            awayhitting[name] = stats
        for tbody in awaypit:
            namelink = tbody.find('td',class_='name').find('a')['href']
            req = requests.get(namelink)
            soup = bs(req.content,'lxml')
            name = soup.find('title').text
            name = name[:name.find('Stats')].strip()
            stats = []
            try:stats.append(tbody.find('td',class_='name').find('a').next_sibling.strip())
            except:stats.append('')
            for td in tbody.findAll('td')[1:]:
                stats.append(td.text)
            awaypitching[name] = stats
            
        
        soup = bs(html,'lxml')
        home = soup.find('div',class_='boxscore-2017__wrap boxscore-2017__wrap--home')
        hometeam = home.find('div',class_='boxscore-2017__team-name').text[:-8]
        homehit = home.find('table',attrs={'data-type':'batting'}).findAll('tbody')[:-1]
        homepit = home.find('table',attrs={'data-type':'pitching'}).findAll('tbody')[:-1]

        homehitting = {}
        homepitching = {}
        for tbody in homehit:
            namelink = tbody.find('td',class_='name').find('a')['href']
            req = requests.get(namelink)
            soup = bs(req.content,'lxml')
            name = soup.find('title').text
            name = name[:name.find('Stats')].strip()
            stats = []
            stats.append(tbody.find('td',class_='name').find('a').next_sibling)
            for td in tbody.findAll('td')[1:]:
                stats.append(td.text)
            homehitting[name] = stats
        for tbody in homepit:
            namelink = tbody.find('td',class_='name').find('a')['href']
            req = requests.get(namelink)
            soup = bs(req.content,'lxml')
            name = soup.find('title').text
            name = name[:name.find('Stats')].strip()
            stats = []
            try:stats.append(tbody.find('td',class_='name').find('a').next_sibling.strip())
            except:stats.append('')
            for td in tbody.findAll('td')[1:]:
                stats.append(td.text)
            homepitching[name] = stats
        
        results_dict = {'AwayTeam':awayteam,
                        'HomeTeam':hometeam,
                        'InnColumns':headers,
                        'AwayScoring':awayrow,
                        'HomeScoring':homerow,
                        'AwayHitting':awayhitting,
                        'AwayPitching':awaypitching,
                        'HomeHitting':homehitting,
                        'HomePitching':homepitching}
        return results_dict
    
    def liveurl(self,query):
        gamesurl = 'https://www.espn.com/mlb/scoreboard'
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(executable_path=driverloc,options=options)
        driver.get(gamesurl)
        html = driver.execute_script("return document.getElementById('events').innerHTML")
        driver.quit()
        soup = bs(html,'lxml')
        allgames = soup.findAll('article')
        liveids_dict = {}
        for box in allgames:
            try:
                if ' '.join(box['class']) == 'scoreboard baseball live js-show':
                    away = box.find('tr',class_='away').find('span',class_='sb-team-short').text
                    home = box.find('tr',class_='home').find('span',class_='sb-team-short').text
                    liveids_dict[away+' at '+home] = box['id']
            except:
                print('some sort of error')
        
        for game in list(liveids_dict.items()):
            if query.lower() in game[0].lower():
                return game[1]
            else:
                pass
        return None
    
    def geturls(self,datein=today):
        gamesurl = 'https://www.espn.com/mlb/scoreboard/_/date/'+datein
        options = Options()
        options.headless = True
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        driver = webdriver.Chrome(executable_path=driverloc,options=options)
        driver.get(gamesurl)
        html = driver.execute_script("return document.getElementById('events').innerHTML")
        driver.quit()
        soup = bs(html,'lxml')
        allgames = soup.findAll('article')
        gamelinks = {}
        for box in allgames:
            try:
                if box['class'][2] == 'final':
                    away = box.findAll('span',class_='sb-team-short')[0].text
                    home = box.findAll('span',class_='sb-team-short')[1].text
                    gameid = box['id']
                    gamelinks[away+' at '+home+' FINAL'] = 'https://www.espn.com/mlb/boxscore/_/gameId/'+gameid
                else:
                    away = box.findAll('span',class_='sb-team-short')[0].text
                    home = box.findAll('span',class_='sb-team-short')[1].text
                    gameid = box['id']
                    gamelinks[away+' at '+home] = 'https://www.espn.com/mlb/boxscore/_/gameId/'+gameid
            except:
                pass
        return gamelinks

    def getids(self,datein=today):
        datein = datein.replace('-','')
        url = 'https://www.espn.com/mlb/scoreboard/_/date/'+datein
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        driver = webdriver.Chrome(executable_path=driverloc,options=options)
        driver.get(url)
        time.sleep(1)
        html = driver.page_source
        driver.quit()
        soup = bs(html,'lxml')
        articles = soup.find('div',id='events').findAll('article')
        gameid_dict = {}
        for article in articles:
            away = article.findAll('span',class_='sb-team-short')[0].text
            home = article.findAll('span',class_='sb-team-short')[1].text
            # if 'live' in ' '.join(article['class']).lower():
            #     gameid_dict['']
            gameid_dict[away+' at '+home] = article['id']
        print(gameid_dict)
    
                    


        
scores = Scores()


#%%




# %%





# %%
