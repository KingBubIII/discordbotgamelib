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

def get_master_and_member_game_data(members, downloaded_only):
    additional_tables = ["","",""]
    if len(members) > 2:
        for count in range(2, len(members)):
            additional_tables[0] += 'JOIN `{0}` as pD{1} '.format(members[count], count)
            additional_tables[1] += ' AND pD{0}.gameID = pD{1}.gameID'.format(count-1,count)
            additional_tables[2] += ' AND pD{0}.downloaded = True AND pD{0}.downloaded = True'.format(count-1,count)
            
    command = 'SELECT * FROM masterGamesList as mD JOIN `{0}` as pD0 JOIN `{1}` as pD1 {2}WHERE mD.gameID=pD0.gameID AND pD0.gameID=pD1.gameID{3}{4}{5}'.format(members[0], members[1], additional_tables[0], additional_tables[1], " AND pD0.downloaded = True AND pD1.downloaded = True" if downloaded_only else "", additional_tables[2] if downloaded_only else "")
    cursor.execute(command)
    return cursor.fetchall()

def profile_update(discord_id, steam_id, discordName):
    command = "SELECT discordID FROM masterUsersList"
    cursor.execute(command)
    all_ids = cursor.fetchall()
    all_ids = [id[0] for id in all_ids]

    new_profile = None
    
    # if profile does not already exists
    if not discord_id in all_ids:
        # sql insert command
        command = "INSERT INTO masterUsersList (discordID, steamID, discordName) VALUES (\'{0}\', \'{1}\', \'{2}\')".format(discord_id, steam_id, discordName)
        new_profile = True
    # if profile does exsist
    else:
        # sql update command
        command = "UPDATE masterUsersList SET steamID=\'{0}\' WHERE discordID=\'{1}\'".format(steam_id, discord_id)
        new_profile = False
    cursor.execute(command)

    # create new table with discord name with same column types of template
    command = "CREATE TABLE IF NOT EXISTS `{0}` LIKE template".format(discordName)
    cursor.execute(command)

    # commit changes to database
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
            if match[6]:
                name_matches.append([match[1],'Downloaded: Yes'])
            else:
                name_matches.append([match[1],'Press {0} to mark as downloaded'.format((count%5)+1), match[0]])
        elif called_from == 'uninstall':
            if not match[6]:
                name_matches.append([match[1],'Downloaded: No'])
            else:
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
    common_games = get_master_and_member_game_data(members, False)

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

def channel_info(channel_name=None):
    command = "SELECT * FROM Channel_Tiers{0}".format("" if channel_name is None else " WHERE ChannelName=`{0}`".format(channel_name))
    cursor.execute(command)

    if not channel_name is None:
        return cursor.fetchone()
    else:
        return cursor.fetchall()

def add_channel(channel_name):
    command = "INSERT INTO Channel_Tiers (ChannelName, Tier) VALUES (\"{0}\", 0)".format(channel_name)
    cursor.execute(command)
    conn.commit()