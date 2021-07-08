#%%
from bs4 import BeautifulSoup as bs
from bs4 import Comment
import lxml
import cchardet
from bs4.builder import HTML_5
import requests
import pandas as pd
from requests.api import head
from unidecode import unidecode as uc
from datetime import datetime as dt

#%%
class Players:
    '''an object representing every single player in MLB history'''
    def __init__(self):
        player_directory = {} # a dictionary with letters of the alphabet as 'keys'. Values will be dictionaries of the 'letter index pages'
        alphabet = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        domain = 'https://www.baseball-reference.com'

        for l in alphabet:
            index = {} 
            sesh = requests.Session()
            req = sesh.get('https://www.baseball-reference.com/'+l+'/')
            soup = bs(req.content,'lxml')
            player_div = soup.find('div',attrs={'id':'div_players_'}).find_all('p')
            for p in player_div:
                full_name = p.find('a').text
                if str(p.findChild())[1] == 'b':
                    status = 'active'
                else:
                    status = 'not active'
                if '+' in p.text:
                    inhof = 'hof'
                else:
                    inhof = 'not-hof'
                op_idx = p.text.find('(')
                index[full_name] = [status,p.text[op_idx+1:-1],inhof,domain+str(p.find('a')['href'])]
            player_directory[l] = index

        self.directory = player_directory

    def geturl(self,query):
        directory = self.directory
        query = str(query.lower())
        if ' ' in query:
            fn_idx = query.find(' ')
            ln_idx = query.rfind(' ')
            first = query[:fn_idx]
            last = query[ln_idx+1:]
            look_in = last[0].lower() # determines which letter index of the directory to search
            possible_matches = []
            relevant_directory = directory[look_in]
            for player,info in relevant_directory.items():
                # this first "if statement" should succeed in covering issues involving unicode text 
                # errors - like if the user inputs or doesn't input a letter with an accent when 
                # one is necessary
                if first in uc(player.lower()) and last in uc(player.lower()) or first in player.lower() and last in player.lower():
                    possible_matches.append((player,info))
                else:
                    pass
            if len(possible_matches) == 1:
                return possible_matches[0][1][3]
            else:
                print('here are the possible matches')
                print('\n')
                for m in possible_matches[0]:
                    print(m[0])
        else:
            print('Maybe try to refine your search?')

    def player(self,query,returndf=True,stats='profile'):

        """ 
        ### if 'returndf' is 'True' (default), method will return a pandas dataframe
        ### if it is marked False, method will return the same information as dict type
        ____________________________________________________________
        ### 'stats' parameter options (if player's PRIMARY positions is/was NOT pitcher') 
        #### --> 'batting', 'fielding', 'psbatting', 'salary'

        ### 'stats' parameter options (if player's PRIMARY position is/was Pitcher') 
        #### --> 'pitching', 'career', 'salary'
        """

        url = self.geturl(query)
        sesh = requests.Session()
        req = sesh.get(url)
        soup = bs(req.content,'lxml')
        stats = stats.lower()

        try:
            pos_area = soup.find('strong',text='Position:').findParent('p').text.lower()
        except:
            try:
                pos_area = soup.find('strong',text='Positions:').findParent('p').text.lower()
            except:
                print("Hmm...Joe might need to fix something in his code")

        first_table_title = soup.findAll('h2')[0].text
        
        if 'pitching' in first_table_title.lower(): # if player's primary position is "Pitcher"
        # if 'pitcher' in pos_area:
            if stats == 'salary':
                comments = soup.find_all(text=lambda text:isinstance(text,Comment)) # comments identified
                headings = []

                for c in comments:
                    if 'Salaries' in c:
                        soup = bs(str(c),'html.parser')
                        salary = soup.find('table')
                        break
                    else:
                        pass
                thead = salary.find('thead').findAll('th')
                headings = []
                for th in thead[1:4]:
                    headings.append(th.text)

                tbody = salary.find('tbody').findAll('tr')
                sal_dict = {}

                for tr in tbody:
                    if tr.text == '':
                        pass
                    else:
                        row_data = []
                        sel_tds = tr.findAll('td')[0:3]
                        for td in sel_tds:
                            row_data.append(td.text)
                        sal_dict[str(tr.find('th').text)] = row_data
                
                if returndf == True:
                    return pd.DataFrame.from_dict(sal_dict,orient='index',columns=headings)
                else:
                    return sal_dict


            elif stats == 'profile':
                profile = soup.find('div',id='meta')
                profile_dict = {}
                short_name = profile.find('h1',attrs={'itemprop':'name'}).text.strip()
                # Full Name
                fullname = profile.find('strong',text='Full Name:').findParent('p').text
                fullname = fullname[fullname.find(':')+1:].strip()

                # Current Team (if applicable)
                try:
                    team = profile.find('strong',text='Team:').findNext('a').text
                except: team = '--'

                # Position(s)
                try:
                    position = profile.find('strong',text='Positions:').findParent('p').text.lower()
                    pos_dict = {'pitcher':'P','catcher':'C','first':'1B','second':'2B','third':'3B','short':'SS','left':'LF','center':'CF','right':'RF','out':'OF','desig':'DH','pinch hitter':'PH'}
                    player_pos = []
                    for key,val in list(pos_dict.items()):
                        if key in position:
                            player_pos.append(val)
                            player_pos.append(', ')
                        else: pass
                    pos_str = ''.join(player_pos[:-1])
                except:
                    try:
                        position = profile.find('strong',text='Position:').findParent('p').text.lower()
                        pos_dict = {'pitcher':'P','catcher':'C','first':'1B','second':'2B','third':'3B','short':'SS','left':'LF','center':'CF','right':'RF','out':'OF','desig':'DH','pinch hitter':'PH'}
                        player_pos = []
                        for key,val in list(pos_dict.items()):
                            if key in position:
                                player_pos.append(val)
                                player_pos.append(', ')
                            else: pass
                        pos_str = ''.join(player_pos[:-1])
                    except: pos_str = '--'
                    
        
                # Date of Birth
                dob = dt.strptime(profile.find('span',attrs={'itemprop':'birthDate'})['data-birth'],'%Y-%m-%d').date()
                
                # Place of Birth
                pob = profile.find('span',attrs={'itemprop':'birthPlace'}).text.strip()[3:]

                # Date of Death (if applicable)
                try:
                    dod = dt.strptime(profile.find('span',attrs={'itemprop':'deathDate'})['data-death'],'%Y-%m-%d').date()
                except:
                    dod = '--'
                
                # Place of Death (if applicable)
                try:
                    pod = profile.find('span',attrs={'itemprop':'deathPlace'}).text.strip()[3:]
                except: pod = '--'
                
                # Height
                height = profile.find('span',attrs={'itemprop':'height'}).text + '"'
                height = height.replace('-',"' ")
                
                # Weight
                weight = profile.find('span',attrs={'itemprop':'weight'}).text + 's'

                # Bats
                bats = profile.find('strong',text='Bats: ').findParent('p').text[6:12]
                bats = bats.strip()
                
                # Throws
                throws = profile.find('strong',text='Throws: ').findParent('p').text
                throws = throws[throws.rfind(':')+1:]
                throws = throws.strip()

                # Debut
                try:
                    debut = profile.find('a',text='Debut:').findParent('strong').findNext('a').findNext('a').text.strip() # might wanna clean this up a bit
                    debut = dt.strptime(debut,r'%B %d, %Y').date()
                except:
                    try:
                        debut = profile.find('strong',text='Debut:').findParent('p').text
                        debut = debut[debut.find(':')+1:debut.find('(')].strip()
                        debut = dt.strptime(debut,r'%B %d, %Y').date()
                        print(debut)
                    except:
                        debut = '--'

                # Debut Age
                try:
                    debut_age = debut.year - dob.year
                except:
                    debut_age = '--'

                # Last Game
                try:
                    last = profile.find('a',text='Last Game:').findParent('strong').findNext('a').findNext('a').text.strip() # might wanna clean this up a bit
                    last = dt.strptime(last,r'%B %d, %Y').date()
                except:
                    last = '--'

                # Last Game Age
                try:
                    lastgame_age = last.year - dob.year
                except:
                    lastgame_age = '--'

                # Rookie Status
                rookie_status = profile.find('a',text='Rookie Status:').findParent('p').text
                try:
                    rookie_status = rookie_status[rookie_status.find(':')+1:rookie_status.find('on')+2].strip()
                except: rookie_status = rookie_status[rookie_status.find(':')+1:rookie_status.find('through')+12].strip()
                

                # Hall of Fame (if applicable)
                try:
                    hof = profile.find('a',text='Hall of Fame').findParent('p').text
                    hof = hof[hof.find(':')+1:hof.find('.')+1].strip()
                except:
                    hof = '--'
                profile_dict = {'FullName':fullname,
                                'CurrentTeam':team,
                                'Pos':pos_str,
                                'DoB':dob,
                                'BornIn':pob,
                                'DoD':dod,
                                'DiedIn':pod,
                                'Height':height,
                                'Weight':weight,
                                'Bats':bats,
                                'Throws':throws,
                                'Debut':debut,
                                'DebutAge':debut_age,
                                'LastGame':last,
                                'LastGameAge':lastgame_age,
                                'RookieStatus':rookie_status,
                                'HoF':hof
                                }
                ## GET IMAGE OBJECT (PICTURE OF EACH PLAYER!)
                if returndf == True:
                    return pd.DataFrame.from_dict(profile_dict,orient='index',columns=[short_name])
                else: return profile_dict
            elif stats == 'pitching':
                headings = []
                thead = soup.find('caption',text='Standard Pitching').findNext('thead').findAll('th')
                for th in thead[1:]:
                    headings.append(th.text)

                tbody = soup.find('caption',text='Standard Pitching').findNext('tbody').findAll('tr')
                pit_dict = {}
                for tr in tbody:
                    row_data = []
                    data = tr.findAll('td')
                    for td in data:
                        row_data.append(td.text)
                    pit_dict[str(tr.find('th').text)+'-'+str(tr.findAll('td')[1].text)] = row_data

                if returndf == True:
                    return pd.DataFrame.from_dict(pit_dict,orient='index',columns=headings)
                else:
                    return pit_dict

            elif stats == 'career':
                thead = soup.find('caption',text='Standard Pitching').findNext('thead').findAll('th')
                headings = []
                for th in thead[4:]:
                    headings.append(th.text)
                tfoot = soup.find('caption',text='Standard Pitching').findNext('tfoot').find('tr')
                row_data = []
                for td in tfoot.findAll('td'):
                    row_data.append(td.text)
                career_dict = {'Career':row_data}

                if returndf == True:
                    return pd.DataFrame.from_dict(career_dict,orient='index',columns=headings)
                else: return career_dict
                

            else:
                print("parameter options are 'pitching', 'career', or 'salary'.\nIt's also possible that this player's primary position might not be Pitcher")



        else: # if player's primary position is NOT "Pitcher"
        # else:
            
            if stats == 'batting':
                thead = soup.find('caption',text='Standard Batting').findNext('thead').findAll('th')
                headings = []
                for th in thead:
                    headings.append(th.text)
                headings = headings[1:]
                tbody = soup.find('caption',text='Standard Batting').findNext('tbody').findAll('tr')
                bat_dict = {}
                for row in tbody:
                    batyear_row = []
                    tds = row.findAll('td')
                    for td in tds:
                        batyear_row.append(td.text)
                    bat_dict[row.find('th').text] = batyear_row
                if returndf == True:
                    df = pd.DataFrame.from_dict(bat_dict,orient='index',columns=headings)
                    return df
                else:
                    return bat_dict
            

            elif stats == 'profile':
                profile = soup.find('div',id='meta')
                profile_dict = {}
                short_name = profile.find('h1',attrs={'itemprop':'name'}).text.strip()
                # Full Name
                fullname = profile.find('strong',text='Full Name:').findParent('p').text
                fullname = fullname[fullname.find(':')+1:].strip()

                # Current Team (if applicable)
                try:
                    team = profile.find('strong',text='Team:').findNext('a').text
                except: team = '--'

                # Position(s)
                try:
                    position = profile.find('strong',text='Positions:').findParent('p').text.lower()
                    pos_dict = {'pitcher':'P','catcher':'C','first':'1B','second':'2B','third':'3B','short':'SS','left':'LF','center':'CF','right':'RF','out':'OF','desig':'DH','pinch hitter':'PH'}
                    player_pos = []
                    for key,val in list(pos_dict.items()):
                        if key in position:
                            player_pos.append(val)
                            player_pos.append(', ')
                        else: pass
                    pos_str = ''.join(player_pos[:-1])
                except:
                    try:
                        position = profile.find('strong',text='Position:').findParent('p').text.lower()
                        pos_dict = {'pitcher':'P','catcher':'C','first':'1B','second':'2B','third':'3B','short':'SS','left':'LF','center':'CF','right':'RF','out':'OF','desig':'DH','pinch hitter':'PH'}
                        player_pos = []
                        for key,val in list(pos_dict.items()):
                            if key in position:
                                player_pos.append(val)
                                player_pos.append(', ')
                            else: pass
                        pos_str = ''.join(player_pos[:-1])
                    except: pos_str = '--'
                    
        
                # Date of Birth
                dob = dt.strptime(profile.find('span',attrs={'itemprop':'birthDate'})['data-birth'],'%Y-%m-%d').date()
                
                # Place of Birth
                pob = profile.find('span',attrs={'itemprop':'birthPlace'}).text.strip()[3:]

                # Date of Death (if applicable)
                try:
                    dod = dt.strptime(profile.find('span',attrs={'itemprop':'deathDate'})['data-death'],'%Y-%m-%d').date()
                except:
                    dod = '--'
                
                # Place of Death (if applicable)
                try:
                    pod = profile.find('span',attrs={'itemprop':'deathPlace'}).text.strip()[3:]
                except: pod = '--'
                
                # Height
                height = profile.find('span',attrs={'itemprop':'height'}).text + '"'
                height = height.replace('-',"' ")
                
                # Weight
                weight = profile.find('span',attrs={'itemprop':'weight'}).text + 's'

                # Bats
                bats = profile.find('strong',text='Bats: ').findParent('p').text[6:12]
                bats = bats.strip()
                
                # Throws
                throws = profile.find('strong',text='Throws: ').findParent('p').text
                throws = throws[throws.rfind(':')+1:]
                throws = throws.strip()

                # Debut
                try:
                    debut = profile.find('a',text='Debut:').findParent('strong').findNext('a').findNext('a').text.strip() # might wanna clean this up a bit
                    debut = dt.strptime(debut,r'%B %d, %Y').date()
                except:
                    try:
                        debut = profile.find('strong',text='Debut:').findParent('p').text
                        debut = debut[debut.find(':')+1:debut.find('(')].strip()
                        debut = dt.strptime(debut,r'%B %d, %Y').date()
                        print(debut)
                    except:
                        debut = '--'

                # Debut Age
                try:
                    debut_age = debut.year - dob.year
                except:
                    debut_age = '--'

                # Last Game
                try:
                    last = profile.find('a',text='Last Game:').findParent('strong').findNext('a').findNext('a').text.strip() # might wanna clean this up a bit
                    last = dt.strptime(last,r'%B %d, %Y').date()
                except:
                    last = '--'

                # Last Game Age
                try:
                    lastgame_age = last.year - dob.year
                except:
                    lastgame_age = '--'

                # Rookie Status
                rookie_status = profile.find('a',text='Rookie Status:').findParent('p').text
                try:
                    rookie_status = rookie_status[rookie_status.find(':')+1:rookie_status.find('on')+2].strip()
                except: rookie_status = rookie_status[rookie_status.find(':')+1:rookie_status.find('through')+12].strip()
                

                # Hall of Fame (if applicable)
                try:
                    hof = profile.find('a',text='Hall of Fame').findParent('p').text
                    hof = hof[hof.find(':')+1:hof.find('.')+1].strip()
                except:
                    hof = '--'
                profile_dict = {'FullName':fullname,
                                'CurrentTeam':team,
                                'Pos':pos_str,
                                'DoB':dob,
                                'BornIn':pob,
                                'DoD':dod,
                                'DiedIn':pod,
                                'Height':height,
                                'Weight':weight,
                                'Bats':bats,
                                'Throws':throws,
                                'Debut':debut,
                                'DebutAge':debut_age,
                                'LastGame':last,
                                'LastGameAge':lastgame_age,
                                'RookieStatus':rookie_status,
                                'HoF':hof
                                }
                ## GET IMAGE OBJECT (PICTURE OF EACH PLAYER!)
                if returndf == True:
                    return pd.DataFrame.from_dict(profile_dict,orient='index',columns=[short_name])
                else: return profile_dict


            elif stats == 'fielding':
                comments = soup.find_all(text=lambda text:isinstance(text,Comment)) # comments identified
                fielding_comments = [] # a list store the necessary comment html for the BATTING tables

                for c in comments: # looks for only the necessary comment blocks for the last few tables
                    if 'Standard Fielding' in c:
                        soup = bs(str(c),'html.parser')
                        fielding_comments.append(soup)
                        break
                    else:
                        pass
                headings = []
                thead = soup.find('caption',text='Standard Fielding').findNext('thead').findAll('th')
                for th in thead:
                    headings.append(th.text)
                tbody = soup.find('caption',text='Standard Fielding').findNext('tbody').findAll('tr')
                field_dict = {}

                for idx,row in enumerate(tbody):
                    tr = row.findAll('td')
                    row_data = []
                    row_data.append(row.find('th').text)
                    for td in tr:
                        row_data.append(td.text)
                    field_dict[str(row.find('th').text)+'-'+str(row_data[3])] = row_data
                if returndf == True:
                    df = pd.DataFrame.from_dict(field_dict,orient='index',columns=headings)
                    return df
                else: return field_dict
            

            elif stats == 'psbatting':
                comments = soup.find_all(text=lambda text:isinstance(text,Comment)) # comments identified
                psbat_comments = [] 
                for c in comments:
                    if 'Postseason Batting' in c:
                        soup = bs(str(c),'html.parser')
                        psbat_comments.append(soup)
                        break
                    else:
                        pass


                headings = []
                thead = soup.find('thead').findAll('th')
                for th in thead[1:]:
                    headings.append(th.text)
                tbody = soup.find('tbody').findAll('tr')
                psbat_dict = {}
                for tr in tbody:
                    row_data = []
                    try:
                        if tr.text == '':
                            pass
                        else:
                            for td in tr.findAll('td'):
                                row_data.append(td.text)
                            psbat_dict[str(tr.find('th').text.replace('\xa0',' '))+'-'+str(row_data[3])] = row_data
                    except:
                        pass
                if returndf == True:
                    return pd.DataFrame.from_dict(psbat_dict,orient='index',columns=headings)
                else:
                    return psbat_dict

            
            elif stats == 'advbatting':
                comments = soup.find_all(text=lambda text:isinstance(text,Comment)) # comments identified
                headings = []
                for c in comments:
                    if 'Advanced Batting' in c:
                        soup = bs(str(c),'html.parser')
                        advbatting = soup.find('table')
                        break
                    else:
                        pass
                thead = advbatting.find('thead').findAll('tr')[1].findAll('th')[9:19] # only the preferred stat headers (HR%, SO%, BB%, LD%, GB%, FB%, GB/FB, Pull%, Cent%, Oppo%)
                for th in thead:
                    headings.append(th.text)
                tbody = advbatting.find('tbody').findAll('tr')
                advbat_dict = {}
                for tr in tbody:
                    sel_tds = tr.findAll('td')[8:18]
                    row_data = []
                    for td in sel_tds:
                        row_data.append(td.text)
                    advbat_dict[str(tr.find('th').text)+'-'+str(tr.find('td',attrs={'data-stat':'team_ID'}).text)] = row_data
                
                if returndf == True:
                    return pd.DataFrame.from_dict(advbat_dict,orient='index',columns=headings)
                else:
                    return advbat_dict

            
            elif stats == 'salary':
                comments = soup.find_all(text=lambda text:isinstance(text,Comment)) # comments identified
                headings = []

                for c in comments:
                    if 'Salaries' in c:
                        soup = bs(str(c),'html.parser')
                        salary = soup.find('table')
                        break
                    else:
                        pass
                thead = salary.find('thead').findAll('th')
                headings = []
                for th in thead[1:4]:
                    headings.append(th.text)

                tbody = salary.find('tbody').findAll('tr')
                sal_dict = {}

                for tr in tbody:
                    if tr.text == '':
                        pass
                    else:
                        row_data = []
                        sel_tds = tr.findAll('td')[0:3]
                        for td in sel_tds:
                            row_data.append(td.text)
                        sal_dict[str(tr.find('th').text)] = row_data
                
                if returndf == True:
                    return pd.DataFrame.from_dict(sal_dict,orient='index',columns=headings)
                else:
                    return sal_dict
                    
            else:
                print("parameter options are 'batting', 'fielding', 'psbatting', or 'salary'")

    def active(self):
        directory = self.directory
        active_ = {}
        for key,value in directory.items():
            active_index = {}
            for k,v in directory[key].items():
                if v[0] == 'active':
                    active_index[k] = v
                else:
                    pass
            active_[key] = active_index
        self.active_ = active_
        return self.active_

    def notactive(self):
        directory = self.directory
        not_active_dir = {}
        for key,value in directory.items():
            active_index = {}
            for k,v in directory[key].items():
                if v[0] == 'not active':
                    active_index[k] = v
                else:
                    pass
            not_active_dir[key] = active_index
        return not_active_dir

    def totalplayers(self):
        directory = self.directory
        total = 0
        for key,value in directory.items():
            for k,v in directory[key].items():
                total+=1
        return total

    def active_num(self):
        directory = self.directory
        total = 0
        for key,value in directory.items():
            for k,v in directory[key].items():
                if v[0] == 'active':
                    total+=1
                else:
                    pass
        return total
    
    def notactive_num(self):
        directory = self.directory
        total = 0
        for key,value in directory.items():
            for k,v in directory[key].items():
                if v[0] == 'not active':
                    total+=1
                else:
                    pass
        return total

player1 = Players().player

#%%






#%%
# TESTING






# %%
# SCRATCH




# %%
