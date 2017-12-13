import PyQt4

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import urllib2, requests
from ghost import Ghost
from contextlib import closing
from selenium.webdriver import Firefox
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

GAME_URL = "http://na.pug.champ.gg/games"
MAIN_URL = "http://na.pug.champ.gg"
B_GAME_URL = "http://na.pug.champ.gg/game/"



# Ideas for future : twilio texts if its a HIGH tier pug
# Auto adding me via text or something



class PugUser:
   '''
        Contains users information, such as id, name, and stats which should be read from file
        Format:
            {class : [1,-1,0..]},
            where the array contains deltas of by how much the player won the game. For example, '1' could mean won
            5-4, 4-3, not 4-2, or 1-1. 
   '''
   #Weights on ELO for classes
   weights = {'Scout':.85,
                  'Roamer':.7,
                  'Pocket':.75,
                  'Demoman':.8,
                  'Medic':.65}

   user_id = -1
   username = ""
   user_stats = {'Scout':[],
                  'Roamer':[],
                  'Pocket':[],
                  'Demoman':[],
                  'Medic':[]}
   weighted_elo = 0
   def get_stats_from_file(self):
       # Loads user_stats
       # If there is nothing, then ELO is auto-0
       pass

   def compute_elo_from_stats(self):
       self.get_stats_from_file()
       if all(len(v) == 0 for v in self.user_stats.values()):
           self.weighted_elo = 0
           return



class PugStruct:
    '''
        Structure order:
            Dictionary of classnames to list of PugUsers
            i.e.
            {'Scout' : [PugUser(b4nny)', ...], 'Soldier' : ['PugUser(shade),...] }
            Updated via update_current_players
    '''
    class_dict = {'Scout':[],
                  'Roamer':[],
                  'Pocket':[],
                  'Demoman':[],
                  'Medic':[]}
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

def get_games_html(url):
    with closing(Firefox(executable_path=r'/home/alex/geckodriver')) as browser:
        browser.get(url)
        WebDriverWait(browser, timeout=50).until(lambda x: x.find_element_by_id("main"))
        arr = browser.page_source.split("<div class=\"flex-3 faction\" id=\"faction-")
        return browser.page_source

def get_game_html(url):
    with closing(Firefox(executable_path=r'/home/alex/geckodriver')) as browser:
        browser.get(url)
        WebDriverWait(browser, timeout=50).until(lambda x: x.find_element_by_id("game"))
        arr = browser.page_source.split("<div class=\"flex-3 faction\" id=\"faction-")
        return browser.page_source



        #print arr[2]
def get_url_html(url):
    with closing(Firefox(executable_path=r'/home/alex/geckodriver')) as browser:
        browser.get(url)
        choice1 = "horizontal layout wrap style-scope pugchamp-launchpad" # should have 6 classes as kids
        choice2 = "style-scope pugchamp-launchpad"
        choice3 = "connected style-scope pugchamp-client" #direct kid of clients
        WebDriverWait(browser, timeout=20).until(EC.presence_of_all_elements_located((By.CLASS_NAME,choice2)))
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
    Gives all current players added up on PugChamp, in a PugStruct
'''

def get_current_games_page():
    url = "http://na.pug.champ.gg/games"
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    f = opener.open(url)
    return f.read()
'''
    Gives the main page's raw HTML
'''
def get_current_main_page():
    with closing(Firefox(executable_path=r'/home/alex/geckodriver')) as browser:
        browser.get(MAIN_URL)
        WebDriverWait(browser, timeout=50).until(lambda x: x.find_element_by_id("main"))

        page_s = browser.page_source
        print page_s#make_current_players(page_s)
    #g = Ghost()
    #with g.start() as session:
    #    page, res = session.open(url)
    #    result, res = session.evaluate("document.body")
    #    print result
    #response = requests.get(url,headers=header)
    #return response.text


def make_current_players(text):
    #<div class="style-scope pugchamp-launchpad"><h3 class="style-scope pugchamp-launchpad">Scout</h3></div>
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

    #print soup
    #h3 class="style-scope pugchamp-launchpad", scout-solly-etc
    #players_html = soup.find_all("div",{"class":"horizontal layout wrap style-scope pugchamp-launchpad"})
    #for a in players_html:
    #    for i in a.find_all("div",{"class":"vertical layout style-scope pugchamp-launchpad"}):
    #        print i
    # div class = horizontal layout wrap style-scope pugchamp-launchpad, id= roles
    #print soup#.find_all("div",{"class":"flex style-scope pugchamp-chat"})
    # <div class="flex style-scope pugchamp-draft"><a target="_blank" class="style-scope pugchamp-draft" href="/player/76561198045772168">tojo</a></div>
    arr = 'flex style-scope pugchamp-draft'#'flex role-column style-scope pugchamp-launchpad'
    #print soup.find('flex style-scope pugchamp-launchpad') # main one
    print player_dict

def get_current_games():
    soup = BeautifulSoup(get_games_html(GAME_URL),'html.parser').find_all("pugchamp-game-summary")
    current_games = []
    for elem in soup:
        current_games.append(B_GAME_URL + elem["game"].split("\"_id\":")[1].split(",")[0].replace("\"", ""))
    return current_games

def get_game_players(game_url):
    player_dict = dict() # player : (class, id)
    soup = BeautifulSoup(get_game_html(game_url),'html.parser')
    factions = soup.find_all("div", {"class": "flex-3 faction"})[2:]
    classes = soup.find_all("div", {"class": "flex-3 faction"})[2].find_all("div")
    for i in factions:
        # first 6 blue, second 6 red
        for c in classes[3:]:
            elem = c
            if elem.h2:
                print elem.h2.text
            else:
                print elem.a.text
                print MAIN_URL + elem.a["href"]
#get_current_main_page()
#soop = BeautifulSoup(get_game_html(get_game_url_from_id("{&quot;_id&quot;:&quot;5a2a4163a6eb5e0e667be77d&quot;,&quot;map&quot;:{&quot;name&quot;:&quot;Gullywash&quot;,&quot;file&quot;:&quot;cp_gullywash_final1&quot;,&quot;image&quot;:&quot;gullywash.png&quot;,&quot;config&quot;:&quot;pugchamp-6v6-standard&quot;,&quot;id&quot;:&quot;gullywash&quot;},&quot;date&quot;:&quot;2017-12-08T07:38:11.515Z&quot;,&quot;status&quot;:&quot;launching&quot;,&quot;teams&quot;:[{&quot;captain&quot;:{&quot;_id&quot;:&quot;594b61f9092628c466323ba0&quot;,&quot;steamID&quot;:&quot;76561198240745690&quot;,&quot;alias&quot;:&quot;Bowserr_&quot;,&quot;admin&quot;:false,&quot;stats&quot;:{},&quot;id&quot;:&quot;594b61f9092628c466323ba0&quot;,&quot;groups&quot;:[]},&quot;faction&quot;:&quot;BLU&quot;},{&quot;captain&quot;:{&quot;_id&quot;:&quot;56f5f7cf7af492d940f6a334&quot;,&quot;steamID&quot;:&quot;76561197970669109&quot;,&quot;alias&quot;:&quot;b4nny&quot;,&quot;admin&quot;:false,&quot;stats&quot;:{},&quot;id&quot;:&quot;56f5f7cf7af492d940f6a334&quot;,&quot;groups&quot;:[]},&quot;faction&quot;:&quot;RED&quot;}],&quot;score&quot;:[],&quot;id&quot;:&quot;5a2a4163a6eb5e0e667be77d&quot;}")), 'html.parser')
#factions = soop.find_all("div", {"class" : "flex-3 faction"})[2:]
#classes = soop.find_all("div", {"class" : "flex-3 faction"})[2].find_all("div")
'''
            '''
#make_current_players(get_url_html(MAIN_URL))
#print get_current_games()
get_game_players("http://na.pug.champ.gg/game/5a2f92c2716b252eb5fb340a")