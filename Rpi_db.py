import pymysql
import ast

#connects to database using username and password
conn = pymysql.connect(user='beastPC', password='SunTitan6//6', host='192.168.1.117')
#cursor allows for commands to be run and collects outputs
cursor = conn.cursor()

def change_db(db_name):
    #choses what database to use
    cursor.execute('USE {0}'.format(db_name));

def SHOW_TABLE(db_name, tbl_name):
    change_db(db_name)
    #view all data in member table
    cursor.execute("SELECT * FROM {0}".format(tbl_name))
    print(cursor.fetchall())

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

def update_db(game_info_dict, tags, multiplayer):

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

    #list comprehention to format it to one dimention list
    searchable_ids = get_game_ids('server','member')
    #print(master_game_data)
    if not game_info_dict["appid"] in searchable_ids:
        #creates string of tuple to insert into members library if its a new game to them.
        channel_data = repr((game_info_dict["appid"], float(game_info_dict["hours_forever"]), 0))
        #print(channel_data)

        #creates command to insert new games into library
        command = "INSERT INTO member ( gameID, hours, downloaded) VALUES {0}"
        #executes command
        cursor.execute(command.format(channel_data))
    else:
        command = "UPDATE member SET hours={0} WHERE gameID={1}"
        #executes command
        cursor.execute(command.format(float(game_info_dict["hours_forever"]), game_info_dict["appid"]))
        
    conn.commit()

    #show the table
    #SHOW_TABLE("masterData","games")
    #print('works')