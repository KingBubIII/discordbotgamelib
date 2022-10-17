from unicodedata import name
import discord
from discord.ext import commands
from discord.ui import Button, View
import pymysql
import steam.steamid as s
from urllib.request import urlopen
import json
import platform
import Rpi_db
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
import time

# http://api.steampowered.com/<interface name>/<method name>/v<version>/?key=<api key>&format=<format>

# Rpi database connection information
username, mypass, host_address = [line.strip() for line in open(('/home/kingbubiii/Documents/discordbotgamelib/' if platform.system() == 'Linux' else '') + 'mysql_login.txt').readlines()]

# connects to database using username and password
conn = pymysql.connect(user=username, password=mypass, host=host_address)
# cursor allows for commands to be run and collects outputs
cursor = conn.cursor()
# select main database
cursor.execute('USE discord_data')

# read steam key from for API access
steamKey = open(('/home/kingbubiii/Documents/discordbotgamelib/' if platform.system() == 'Linux' else '') + 'steam_key.txt').readline()

# basic URL to be formatted with steamkey and player steam id
basicURL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={0}&steamid={1}&include_played_free_games=true&format=json"

# store the response of URL open
response = urlopen("http://api.steampowered.com/ISteamApps/GetAppList/v0002/")

# storing the JSON response 
name_lookup = json.loads(response.read())["applist"]["apps"]

# function to be called both internally and externally
def update_lib(discordName):
    #start = time.time()

    command = "CREATE TABLE IF NOT EXISTS `{0}` LIKE template".format(discordName)
    cursor.execute(command)

    # get steam ID with discord name lookup
    command = "SELECT steamID FROM masterUsersList WHERE discordName=\'{0}\'".format(discordName)
    cursor.execute(command)
    steamID = cursor.fetchone()[0]

    # formats the URL
    all_games_url = basicURL.format(steamKey, steamID)

    # store the response of URL open
    response = urlopen(all_games_url)

    # storing the JSON response 
    data_json = json.loads(response.read())

    # looping through each game
    for game in data_json['response']['games']:
        
        # checks if game needs can update user's infomation
        if game['appid'] in Rpi_db.get_game_ids(discordName):
            #sql command to update hours
            command = "UPDATE `{0}` SET hours={1} WHERE gameID={2}".format(discordName, game['playtime_forever']/60, game['appid'])
        # else checks if the game is in the master game lookup table but not in user's table
        elif game['appid'] in Rpi_db.get_game_ids("masterGamesList"):
            # formats data to include "()" for sql reasons
            new_game_data = repr((game["appid"], float(game["playtime_forever"]/60), 0))
            # create new row for new game in user's table
            command = "INSERT INTO `{0}` ( gameID, hours, downloaded) VALUES {1}".format(discordName, new_game_data)
        # else add to master lookup table
        else:
            steam_game_link = 'https://store.steampowered.com/app/' + str(game['appid'])
            
            # opens connection to client website and downloads information
            uClient = uReq(steam_game_link)

            # loads html content into variable
            page_html = uClient.read()
            # closes connection to client website
            uClient.close()

            # parse the html document, making soup object
            page_soup = soup(page_html, "html.parser")

            # finds all game tags
            json_script = page_soup.find_all("a", class_="app_tag")
            tags = []
            multiplayer = False
            # loops through all tags
            for tag in json_script:
                # gets rid of extra characters
                tag = tag.next.strip()
                # adds tag to list
                tags.append(tag)
                # checks if multiplayer 
                if tag == "Multiplayer":
                    db_multiplayer = True

            gameName = ""
            for item in name_lookup:
                if item["appid"] == game["appid"]:
                    gameName = item["name"]

            
            # list of trademarks that become weird strings after webscrapping
            trademarks = ['u00ae','u2122']

            #loops through tradesmarks
            for trademark in trademarks:
                # if trademark is in the game name
                if trademark in gameName:
                    # replace string with trademark character
                    gameName = gameName.replace(trademark,chr(int(trademark.replace('u',''), 16)))

            #created string of tuple to insert into master data if it does not exsist in database already
            data_input = repr((game["appid"], gameName, multiplayer, ",".join(tags)))

            #creates command to insert new games into library
            command = "INSERT INTO masterGamesList ( gameID, gameName, multiplayer, tags) VALUES {0}".format(data_input)
            cursor.execute(command)
            # formats data to include "()" for sql reasons
            new_game_data = repr((game["appid"], float(game["playtime_forever"]/60), 0))
            # create new row for new game in user's table
            command = "INSERT INTO `{0}` ( gameID, hours, downloaded) VALUES {1}".format(discordName, new_game_data)

        cursor.execute(command)
        conn.commit()
    #print(time.time() - start)
        

def main():
    # sql command to show all member library tables
    command = "SELECT discordName FROM masterUsersList"
    cursor.execute(command)
    # return all names
    results = cursor.fetchall()
    # formats into list
    members = [result[0] for result in results]
    # updates each members library
    for member in members:
        #print(member)
        update_lib(member)

if __name__ == "__main__":
    main()