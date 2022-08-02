import pymysql
import ast

from scipy.fft import idct

#connects to database using username and password
conn = pymysql.connect(user='beastPC', password='SunTitan6//6', host='192.168.1.117')
#cursor allows for commands to be run and collects outputs
cursor = conn.cursor()

def change_db(db_name):
    #choses what database to use
    cursor.execute('USE `{0}`'.format(db_name));

def show_table(db_name, tbl_name):
    change_db(db_name)
    #view all data in member table
    cursor.execute("SELECT * FROM `{0}`".format(tbl_name))
    for item in cursor.fetchall():
        print(*item)

def get_game_ids(db_name,tbl_name):
    change_db(db_name)

    #command to get list of ids in user library
    command = "SELECT {0} FROM {1}".format('steamID' if db_name=='masterData' else 'gameID', 'games' if db_name=='masterData' else tbl_name)
    #execute
    cursor.execute(command)
    #gets results into variable
    results = cursor.fetchall()

    #list comprehention to format it to one dimention list
    searchable_ids = [ int(result[0]) for result in results ]

    return searchable_ids

def update_db(server, discord_name, game_info_dict, tags, multiplayer):

    #get list of all ids in master data
    master_game_ids = get_game_ids('masterData','games')
    
    if not game_info_dict["appid"] in master_game_ids:
        #created string of tuple to insert into master data if it does not exsist in database already
        master_game_data = repr((game_info_dict["appid"], game_info_dict["name"], multiplayer, tags))

        change_db('masterData')
        #creates command to insert new games into library
        command = "INSERT INTO games ( steamID, gameName, multiplayer, tags) VALUES {0}"
        #executes command
        cursor.execute(command.format(master_game_data))

    #checking if the server database exists
    command = "SHOW DATABASES WHERE `database` = \'{0}\'".format(server)
    cursor.execute(command)
    db_exists = True if not len(cursor.fetchall()) == 0 else False
    
    #create the database if it does not exist
    if not db_exists:
        command = "CREATE DATABASE `{0}`".format(server)
        cursor.execute(command)
        conn.commit()
    
    #checks if the member exists
    change_db(server)
    command = "SHOW TABLES LIKE \'{0}\'".format(discord_name)
    cursor.execute(command)
    tbl_exists = True if not len(cursor.fetchall()) == 0 else False

    if not tbl_exists:
        command = "CREATE TABLE `{0}` LIKE server.member".format(discord_name)
        cursor.execute(command)
        conn.commit()

    #list comprehention to format it to one dimention list
    searchable_ids = get_game_ids(server,discord_name)
    #print(master_game_data)
    if not game_info_dict["appid"] in searchable_ids:
        #creates string of tuple to insert into members library if its a new game to them.
        channel_data = repr((game_info_dict["appid"], float(game_info_dict["hours_forever"]), 0))
        #print(channel_data)

        #creates command to insert new games into library
        command = "INSERT INTO {0} ( gameID, hours, downloaded) VALUES {1}".format(discord_name, channel_data)
        #executes command
        cursor.execute(command)
    else:
        command = "UPDATE {0} SET hours={1} WHERE gameID={2}".format(discord_name, float(game_info_dict["hours_forever"]), game_info_dict["appid"])
        #executes command
        cursor.execute(command)
        
    conn.commit()


def profile_update(discord_id, steam_id):
    change_db('masterData')
    command = "SELECT discordID FROM members"
    cursor.execute(command)
    all_ids = cursor.fetchall()
    all_ids = [id[0] for id in all_ids]

    new_profile = None
    
    if not discord_id in all_ids:
        command = "INSERT INTO members (discordID, steamID) VALUES (\'{0}\', \'{1}\')".format(discord_id, steam_id)
        new_profile = True
    else:
        command = "UPDATE members SET steamID=\'{0}\' WHERE discordID=\'{1}\'".format(steam_id, discord_id)
        new_profile = False

    cursor.execute(command)
    conn.commit()
    return new_profile

def format_details(formatting=None):
    formatted_details = ""
    #default choice if no formatting option is specified
    if formatting == None:
        formatted_details = 'Downloaded: (d)'
    #user specified formatting
    else:
        #loops through each choice
        for char in formatting:
            #formats all details if 'a' is selected
            if char == 'a':
                formatted_details += 'Hours: (h)'+'\n'+'Online: (o)'+'\n'+'Downloaded: (d)' +'\n'+ 'Tags: (t)'
                break
            #other options format their respective details
            else:
                #hour count playing the game
                if char == 'h':
                    formatted_details += 'Hours: (h)'
                #shows if its multiplayer compatable
                if char == 'o':
                    formatted_details += 'Online: (o)'
                #shows if the mentioned user currently has it downloaded
                if char == 'd':
                    formatted_details += 'Downloaded: (d)'
                if char == 't':
                    formatted_details += 'Tags: (t)'
                #adds new line character after each detail is formated for readability
                if not char == formatting[-1]:
                    formatted_details += '\n'
    return formatted_details

def readlib(server, libclass, formatting=None):
    #select server database
    change_db(server)
    #chose order despending on if the hours formatting option is shown
    orderby = 'mD.gameName ASC' if (formatting==None or not 'h' in formatting) else 'sD.hours DESC'
    #get a list of each game in the library and its master data with it 
    command = "SELECT mD.*, sD.* FROM masterData.games AS mD, `{0}`.`{1}` as sD WHERE mD.steamID = sD.gameID ORDER BY {2}".format(server, libclass.User, orderby)
    cursor.execute(command)
    #get the result
    all_games = cursor.fetchall()

    #loop through each game
    for game in all_games:
        #chose human readable outputs
        downloaded = 'Yes' if game[6] else "No"
        hours = str(game[5])
        multiplayer = 'Yes' if game[2] else "No"
        tags = game[3]
        formatted_details = format_details(formatting)
        formatted_details = formatted_details.replace('(d)',downloaded).replace('(h)',hours).replace('(o)',multiplayer).replace('(t)',tags)
        
        #temperary array
        data = [game[1],formatted_details]
        #add game and the details that have been formatted to library class data
        libclass.data_array.append(data)

def get_steam_link(member_class):
    change_db('masterData')
    command = 'SELECT steamID FROM members WHERE discordID={0}'.format(member_class.id)
    cursor.execute(command)
    steam_id = cursor.fetchone()[0]
    link = "https://steamcommunity.com/profiles/" + str(steam_id) + "/games/?tab=all"
    return link

def search(server, member, query):
    name_matches = []
    change_db('masterData')
    command = 'SELECT * FROM games WHERE gameName LIKE \'{0}%\''.format(query)
    if len(query) > 1:
        command = command.replace('\'','\'%',1)
    cursor.execute(command)
    master_matches = cursor.fetchall()

    change_db(server)
    
    for game in master_matches:
        command = 'SELECT * FROM {0} WHERE gameID=\'{1}\''.format(member, game[0])
        cursor.execute(command)
        local_match = cursor.fetchall()

        if len(local_match) == 0:
            continue
        else:
            downloaded = 'Yes' if local_match[0][2] else "No"
            name_matches.append([game[1],format_details().replace('(d)',downloaded)])
    return name_matches