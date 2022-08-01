import pymysql
import ast

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

#show the table
#show_table("server","member")
#print('works')