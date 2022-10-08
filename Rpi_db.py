import pymysql
import platform
import time

# gets all host connection info from local file
# uses linux or windows paths as needed
username, mypass, host_address = [line.strip() for line in open(('/home/kingbubiii/Documents/discordbotgamelib/' if platform.system() == 'Linux' else '') + 'mysql_login.txt').readlines()]

#connects to database using username and password
conn = pymysql.connect(user=username, password=mypass, host=host_address)
#cursor allows for commands to be run and collects outputs
cursor = conn.cursor()
cursor.execute('USE discord_data')

def show_table(db_name, tbl_name):
    #view all data in member table
    cursor.execute("SELECT * FROM `{0}`".format(tbl_name))
    for item in cursor.fetchall():
        print(*item)

def get_game_ids(tbl_name):
    #command to get list of ids in user library
    command = "SELECT `{0}` FROM `{1}`".format('steamID' if tbl_name=='masterUsersList' else 'gameID', tbl_name)
    #execute
    cursor.execute(command)
    #gets results into variable
    results = cursor.fetchall()

    #list comprehention to format it to one dimention list
    searchable_ids = [ int(result[0]) for result in results ]

    return searchable_ids

def get_all_members():
    command = 'SELECT discordID FROM masterUsersList'
    cursor.execute(command)
    membersID_list = [ row[0] for row in cursor.fetchall() ]
    return membersID_list

def update_db(discord_name, game_info_dict, tags, multiplayer):

    #get list of all ids in master data
    master_game_ids = get_game_ids('masterGamesList')
    
    if not game_info_dict["appid"] in master_game_ids:
        #created string of tuple to insert into master data if it does not exsist in database already
        master_game_data = repr((game_info_dict["appid"], game_info_dict["name"], multiplayer, tags))

        #creates command to insert new games into library
        command = "INSERT INTO masterGamesList ( gameID, gameName, multiplayer, tags) VALUES {0}"
        #executes command
        cursor.execute(command.format(master_game_data))
    
    #checks if the member exists
    command = "CREATE TABLE IF NOT EXISTS `{0}` LIKE template".format(discord_name)
    cursor.execute(command)

    #list comprehention to format it to one dimention list
    searchable_ids = get_game_ids(discord_name)
    #print(master_game_data)
    if not game_info_dict["appid"] in searchable_ids:
        #creates string of tuple to insert into members library if its a new game to them.
        channel_data = repr((game_info_dict["appid"], float(game_info_dict["hours_forever"].replace(",","")), 0))
        #print(channel_data)

        #creates command to insert new games into library
        command = "INSERT INTO `{0}` ( gameID, hours, downloaded) VALUES {1}".format(discord_name, channel_data)
        #executes command
        cursor.execute(command)
    else:
        command = "UPDATE `{0}` SET hours={1} WHERE gameID={2}".format(discord_name, float(game_info_dict["hours_forever"].replace(',','')), game_info_dict["appid"])
        #executes command
        cursor.execute(command)
        
    conn.commit()

def profile_update(discord_id, steam_id, discordName):
    command = "SELECT discordID FROM masterUsersList"
    cursor.execute(command)
    all_ids = cursor.fetchall()
    all_ids = [id[0] for id in all_ids]

    new_profile = None
    
    if not discord_id in all_ids:
        command = "INSERT INTO masterUsersList (discordID, steamID, discordName) VALUES (\'{0}\', \'{1}\', \'{2}\')".format(discord_id, steam_id, discordName)
        new_profile = True
    else:
        command = "UPDATE masterUsersList SET steamID=\'{0}\' WHERE discordID=\'{1}\'".format(steam_id, discord_id)
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

def readlib(libclass, formatting=None):
    #chose order despending on if the hours formatting option is shown
    orderby = 'gameName ASC' if (formatting==None or not 'h' in formatting) else 'hours DESC'
    #get a list of each game in the library and its master data with it 
    #command = "SELECT mD.*, sD.* FROM masterData.games AS mD, `{0}`.`{1}` as sD WHERE mD.steamID = sD.gameID ORDER BY {2}".format(server, libclass.User, orderby)
    command = "SELECT * FROM masterGamesList as mD JOIN `{0}` as pD WHERE mD.gameID = pD.gameID ORDER BY {1}".format(libclass.User, orderby)
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
    command = 'SELECT steamID FROM masterUsersList WHERE discordID={0}'.format(member_class.id)
    cursor.execute(command)
    steam_id = cursor.fetchone()[0]
    link = "https://steamcommunity.com/profiles/" + str(steam_id) + "/games/?tab=all"
    return link

def search(member, query, called_from):
    name_matches = []
    if query != None:
        if len(query) > 1:
            query = '%' + query
        query = " AND gameName LIKE \"{0}%\"".format(query)
    else:
        query = ""
    
    if called_from == "uninstall":
        query += " AND pD.downloaded=1"
    #command = 'SELECT * FROM games JOIN `{0}`.`{1}` WHERE gameID=steamID{2} ORDER BY gameName ASC'.format(server, member, query)
    command = 'SELECT * FROM masterGamesList as mD JOIN `{0}` as pD WHERE mD.gameID = pD.gameID{1} ORDER BY gameName ASC'.format(member, query)
    cursor.execute(command)
    matches = cursor.fetchall()

    for count, match in enumerate(matches):
        #downloaded = 'Yes' if match[6] else 'No'
        if called_from == 'download':
            name_matches.append([match[1],'Press {0} to mark as downloaded'.format((count%5)+1), match[0]])
        elif called_from == 'uninstall':
            name_matches.append([match[1],'Press {0} to mark as uninstalled'.format((count%5)+1), match[0]])
        elif called_from == 'search':
            name_matches.append([match[1],'\u200b'])
        #name_matches.append([match[1],format_details().replace('(d)',downloaded), match[0]])
        
    return name_matches

def mark_as(member, game_id, set_as):
    command = "UPDATE `{0}` SET downloaded={1} WHERE gameID={2}".format(member, 1 if set_as else 0, game_id)
    cursor.execute(command)
    conn.commit()
    
    command = "SELECT gameName, downloaded FROM `masterGamesList` as mD JOIN `{0}` as pD WHERE mD.gameID = '{1}' AND pD.gameID = '{1}'".format(member, game_id)
    cursor.execute(command)
    return cursor.fetchone()

def compare(members, libclass, format):
    additional_tables = ["","",""]
    if len(members) > 2:
        for count in range(2, len(members)):
            additional_tables[0] += 'JOIN `{0}` as pD{1} '.format(members[count], count)
            additional_tables[1] += ' AND pD{0}.gameID = pD{1}.gameID'.format(count-1,count)
            """
            additional_tables[0] += ', pD{0}.*'.format(count)
            additional_tables[1] += ', `{0}`.`{1}` as pD{2}'.format(server, members[count], count)
            additional_tables[2] += ' AND pD{0}.gameID = pD{1}.gameID'.format(count-1,count)
    command = 'SELECT mD.*, pD0.*, pD1.*{3} FROM masterData.games as mD, `{0}`.`{1}` AS pD0, `{0}`.`{2}` as pD1{4} WHERE mD.steamID = pD0.gameID AND pD0.gameID = pD1.gameID{5}'.format(server, members[0], members[1], additional_tables[0], additional_tables[1], additional_tables[2])
    """
    command = 'SELECT * FROM masterGamesList as mD JOIN `{0}` as pD0 JOIN `{1}` as pD1 {2}WHERE mD.gameID=pD0.gameID AND pD0.gameID=pD1.gameID{3}'.format(members[0], members[1], additional_tables[0], additional_tables[1], additional_tables[2])
    cursor.execute(command)
    common_games = cursor.fetchall()

    #loop through each game
    for game in common_games:
        all_member_details = []
        for member_index in range(len(members)):

            #chose human readable outputs
            downloaded = 'Yes' if game[3+(3*(member_index+1))] else "No"
            hours = str(game[2+(3*(member_index+1))])
            multiplayer = 'Yes' if game[2] else "No"
            tags = game[3]
            formatted_details = format_details(format)
            formatted_details = formatted_details.replace('(d)',downloaded).replace('(h)',hours).replace('(o)',multiplayer).replace('(t)',tags)
            all_member_details.append(formatted_details)
        #temperary array
        data = [game[1],all_member_details]
        #add game and the details that have been formatted to library class data
        libclass.data_array.append(data)