import json
import pprint
import urllib3
import sys
from contextlib import closing

from bs4 import BeautifulSoup
from enum import Enum
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

GAME_URL = "http://na.pug.champ.gg/games"
MAIN_URL = "http://na.pug.champ.gg"
B_GAME_URL = "http://na.pug.champ.gg/game/"
GECKO_PATH = r'/home/alex/geckodriver' if sys.platform is "posix" else "C:\\Users\\Alex\\Downloads\\geckodriver-v0.21.0-win64\\geckodriver.exe"
LOGS_PLAYER_URL = "http://logs.tf/api/v1/log?player="

# Things to consider: python 'fluentwait' for selenium.
# TODO: get consistent querying going for WebDriverWait
# File storage of GameData and PugUser

http = urllib3.PoolManager()

class PugClass(Enum):
    Scout = 0
    Roamer = 1
    Pocket = 2
    Demoman = 3
    Medic = 4
    
weights = {PugClass.Scout: .85,
           PugClass.Roamer: .7,
           PugClass.Pocket: .75,
           PugClass.Demoman: .8,
           PugClass.Medic: .65}



class GameData:
    '''
        Contains metadata about each game played, such as game_id, storage of {PugUser:Class}, logs page, and local storage of logs
    '''
    game_id = -1
    class_data = {} # PugUser:Class
    logs_page = ""
    logs_data = None # Some logs object..

class PugUser:
   '''
        Contains users information, such as id, name, and stats which should be read from file
        (Potential) Format:
            {class : [1,-1,0..]},
            where the array contains deltas of by how much the player won the game. For example, '1' could mean won
            5-4, 4-3, not 4-2, or 1-1. 
   '''
   #Weights on ELO for classes
   def __init__(self, sid, user):
       self.steamid64 = sid
       self.username = user

   steamid64 = "" # is the ID pugchamp uses
   username = ""
   #{Class:  ELO for class}
   user_stats = dict((c, 0) for c in PugClass)
   weighted_elo = 0
   newest_checked_log_id = 0 # Link to the last log user played in, updated every once in a while
   def update_stats_from_logs(self):
       # Query logs.tf for this players logs (STEAMID64)
       player_logs = json.loads(http.request("GET", LOGS_PLAYER_URL + self.steamid64 + "&limit=10000").data.decode("UTF-8"))
       logs_array = player_logs["logs"][::-1]
       print(logs_array)
       for log in logs_array:
            log_id = int(json.load(log)["id"])
            if self.newest_checked_log_id != 0 and log_id < self.newest_checked_log_id:
                continue # not sure if I will need to calculate ELO differently for those who have not been calculated
                # vs those who just need logs updated.
            log_json = http.request("GET", LOGS_URL + str(log_id))
            name_map = log_json["names"]
            player_id = -1
            for id, name in name_map:
                if name == self.username:
                    player_id = id
            player_stats = log_json["players"][player_id]
            # Do ELO stuff here...
            self.newest_checked_log_id = log_id

   def compute_elo_from_stats(self):
       self.update_stats_from_logs()
       if all(v for v in self.user_stats.values()):
           self.weighted_elo = 0
       else:
           for tf2class in weights:
               self.weighted_elo += (self.user_stats[tf2class] * weights[tf2class]) / 4
               # mega arbitrary, do more with this



class PugStruct:
    '''
        Structure order:
            Dictionary of classnames to list of PugUsers
            i.e.
            {'Scout' : [PugUser(b4nny)', ...], 'Soldier' : ['PugUser(shade),...] }
            Updated via update_current_players
    '''
    class_dict = {PugClass.Scout:[],
                  PugClass.Roamer:[],
                  PugClass.Pocket:[],
                  PugClass.Demoman:[],
                  PugClass.Medic:[]}
    '''
        Uses a weighted system based on each users records based on wins / losses recorded locally due to lack of ELO
        For example, if there are lots of low ELO players but good medics, there is an overall less likely recommendation to add
        If there are generally higher ELO players, it recommends to add
        Tiers : ['A+', 'A', 'B+', 'B', 'C+', 'C', 'Bad']
    '''
    weighted_elo = 0
    online_users = 0
    # returns current tier of pug based on ELO
    def tier(self):
        tier_list =  ['A+', 'A', 'B+', 'B', 'C+', 'C', 'Bad']
        selector = {
            self.weighted_elo < 50: tier_list[6],
            50 <= self.weighted_elo < 60: tier_list[5],
            60 <= self.weighted_elo < 70: tier_list[4],
            70 <= self.weighted_elo < 75: tier_list[3],
            75 <= self.weighted_elo < 80: tier_list[2],
            80 <= self.weighted_elo < 90: tier_list[1],
            90 <= self.weighted_elo: tier_list[0],
        }[1]
        return selector
    # returns list of current PugUsers
    def get_current_players(self):
        ret = set([user for user in self.class_dict.values()])
        self.online_users = len(ret)
        return ret

    # updates weighted_elo based on players
    # currently just averaging
    def update_elo(self):
        self.weighted_elo = sum(map(lambda x : x.weighted_elo, self.get_current_players())) / self.online_users

'''
    :return HTML for the overall /games page or a specific one if given
'''
def get_games_html(url=GAME_URL):
    with closing(Firefox(executable_path=GECKO_PATH)) as browser:
        browser.get(url)
        WebDriverWait(browser, timeout=50).until(lambda x: x.find_element_by_id("main"))
        arr = browser.page_source.split("<div class=\"flex-3 faction\" id=\"faction-")
        return browser.page_source

'''
    :return HTML for main page for pugchamp
'''
def get_url_html(url=MAIN_URL):
    with closing(Firefox(executable_path=GECKO_PATH)) as browser:
        browser.get(url)
        choice1 = "horizontal layout wrap style-scope pugchamp-launchpad" # should have 6 classes as kids
        choice2 = "style-scope pugchamp-launchpad"
        choice3 = "connected style-scope pugchamp-client" #direct kid of clients
        WebDriverWait(browser, timeout=20, poll_frequency=5).until(EC.presence_of_all_elements_located((By.CLASS_NAME,choice2)))
        #or ..

        return browser.page_source
        #print arr[2]

def get_game_url_from_id(game_str):
    # Example str:
    base = "http://na.pug.champ.gg/game/"
    quot_split = game_str.split("&quot;")
    return base + quot_split[3]
    # "{&quot;_id&quot;:&quot;5a2a4163a6eb5e0e667be77d&quot;,&quot;map&quot;:{&quot;name&quot;:&quot;Gullywash&quot;,&quot;file&quot;:&quot;cp_gullywash_final1&quot;,&quot;image&quot;:&quot;gullywash.png&quot;,&quot;config&quot;:&quot;pugchamp-6v6-standard&quot;,&quot;id&quot;:&quot;gullywash&quot;},&quot;date&quot;:&quot;2017-12-08T07:38:11.515Z&quot;,&quot;status&quot;:&quot;launching&quot;,&quot;teams&quot;:[{&quot;captain&quot;:{&quot;_id&quot;:&quot;594b61f9092628c466323ba0&quot;,&quot;steamID&quot;:&quot;76561198240745690&quot;,&quot;alias&quot;:&quot;Bowserr_&quot;,&quot;admin&quot;:false,&quot;stats&quot;:{},&quot;id&quot;:&quot;594b61f9092628c466323ba0&quot;,&quot;groups&quot;:[]},&quot;faction&quot;:&quot;BLU&quot;},{&quot;captain&quot;:{&quot;_id&quot;:&quot;56f5f7cf7af492d940f6a334&quot;,&quot;steamID&quot;:&quot;76561197970669109&quot;,&quot;alias&quot;:&quot;b4nny&quot;,&quot;admin&quot;:false,&quot;stats&quot;:{},&quot;id&quot;:&quot;56f5f7cf7af492d940f6a334&quot;,&quot;groups&quot;:[]},&quot;faction&quot;:&quot;RED&quot;}],&quot;score&quot;:[],&quot;id&quot;:&quot;5a2a4163a6eb5e0e667be77d&quot;}"


'''
    Gives the main page's raw HTML
'''
def get_current_main_page():
    with closing(Firefox(executable_path=GECKO_PATH)) as browser:
        browser.get(MAIN_URL)
        WebDriverWait(browser, timeout=50).until(lambda x: x.find_element_by_id("main"))

        page_s = browser.page_source
        print(page_s)
        return page_s

def get_current_draft():
    url=MAIN_URL
    with closing(Firefox(executable_path=GECKO_PATH)) as browser:
        browser.get(url)
        choice1 = "horizontal layout wrap style-scope pugchamp-draft"  # should have 6 classes as kids
        choice2 = "style-scope pugchamp-launchpad"
        choice3 = "connected style-scope pugchamp-client"  # direct kid of clients
        try:
            WebDriverWait(browser, timeout=20).until(EC.presence_of_element_located((By.CLASS_NAME, "x-scope pugchamp-launchpad-0")))
        except TimeoutException:
            print("No pug currently going..")
            return
        html = browser.page_source
        make_current_players(html)
        #for i in BeautifulSoup(html).find_all("paper-material", {"class": "style-scope pugchamp-launchpad x-scope paper-material-0"}):
        #    print i

def make_current_players(url=MAIN_URL):
    text = get_url_html(url)
    player_dict = dict() # (player) : ([classes], page)
    soup = BeautifulSoup(text,'html.parser')
    roles = soup.find("div",{"class":"horizontal layout wrap style-scope pugchamp-launchpad"},id='roles')
    for role in roles.find_all("div",{"class":"vertical layout style-scope pugchamp-launchpad"}):
        cls = role.find("h3",{"class":"style-scope pugchamp-launchpad"}).text
        players = role.find_all("a",{"target":"_blank"})
        for p in players:
            if p.text not in player_dict:
                player_dict[p.text] = ([cls], MAIN_URL+p['href'])
            else:
                player_dict[p.text][0].append(cls)

    arr = 'flex style-scope pugchamp-draft'#'flex role-column style-scope pugchamp-launchpad'
    pprint.pprint(player_dict)

def get_current_games():
    soup = BeautifulSoup(get_games_html(GAME_URL),'html.parser').find_all("pugchamp-game-summary")
    current_games = []
    for elem in soup:
        current_games.append(B_GAME_URL + elem["game"].split("\"_id\":")[1].split(",")[0].replace("\"", ""))
    return current_games

def pug_is_launching():
    with closing(Firefox(executable_path=GECKO_PATH)) as browser:
        browser.get(MAIN_URL)
        WebDriverWait(browser, timeout=30).until(EC.presence_of_element_located((By.ID,"ready")))
        html = browser.page_source
        for element in browser.find_elements_by_tag_name("h2"):
            if element.get_attribute("textContent") == 'Launch In Progress' and element.is_displayed():
                print("Pickings")
                #make_current_players(html)
                return True
        print("No picks")
        return False


def get_game_players(game_url):
    player_dict = dict() # player : (class, id)
    soup = BeautifulSoup(get_games_html(game_url),'html.parser')
    factions = soup.find_all("div", {"class": "flex-3 faction"})[2:]
    classes = soup.find_all("div", {"class": "flex-3 faction"})[2].find_all("div")
    for i in factions:
        # first 6 blue, second 6 red
        most_recent_class = ""
        for elem in classes[3:]:
            if elem.h2:
                most_recent_class = elem.h2.text
            else:
                player_dict[elem.a.text] = (most_recent_class, MAIN_URL + elem.a["href"])
    return player_dict

def get_log_by_id(id):
    rq = http.request('GET', LOGS_URL + id).data
    print(rq)
    return json.loads(rq.decode("UTF-8"))


#get_current_main_page()
#soop = BeautifulSoup(get_game_html(get_game_url_from_id("{&quot;_id&quot;:&quot;5a2a4163a6eb5e0e667be77d&quot;,&quot;map&quot;:{&quot;name&quot;:&quot;Gullywash&quot;,&quot;file&quot;:&quot;cp_gullywash_final1&quot;,&quot;image&quot;:&quot;gullywash.png&quot;,&quot;config&quot;:&quot;pugchamp-6v6-standard&quot;,&quot;id&quot;:&quot;gullywash&quot;},&quot;date&quot;:&quot;2017-12-08T07:38:11.515Z&quot;,&quot;status&quot;:&quot;launching&quot;,&quot;teams&quot;:[{&quot;captain&quot;:{&quot;_id&quot;:&quot;594b61f9092628c466323ba0&quot;,&quot;steamID&quot;:&quot;76561198240745690&quot;,&quot;alias&quot;:&quot;Bowserr_&quot;,&quot;admin&quot;:false,&quot;stats&quot;:{},&quot;id&quot;:&quot;594b61f9092628c466323ba0&quot;,&quot;groups&quot;:[]},&quot;faction&quot;:&quot;BLU&quot;},{&quot;captain&quot;:{&quot;_id&quot;:&quot;56f5f7cf7af492d940f6a334&quot;,&quot;steamID&quot;:&quot;76561197970669109&quot;,&quot;alias&quot;:&quot;b4nny&quot;,&quot;admin&quot;:false,&quot;stats&quot;:{},&quot;id&quot;:&quot;56f5f7cf7af492d940f6a334&quot;,&quot;groups&quot;:[]},&quot;faction&quot;:&quot;RED&quot;}],&quot;score&quot;:[],&quot;id&quot;:&quot;5a2a4163a6eb5e0e667be77d&quot;}")), 'html.parser')
#factions = soop.find_all("div", {"class" : "flex-3 faction"})[2:]
#classes = soop.find_all("div", {"class" : "flex-3 faction"})[2].find_all("div")
'''
            '''
#pug_is_launching()
#print get_game_players()
make_current_players()
#pprint.pprint(get_log_by_id("1"))#print get_current_games()
#print(get_game_players("http://na.pug.champ.gg/game/5a2f92c2716b252eb5fb340a"))
#yosh = PugUser(sid="76561198039891603", user="yosh")
#yosh.update_stats_from_logs()