#!/usr/bin/python3
from cgitb import reset
from threading import TIMEOUT_MAX
from typing import List
import discord
from discord.ext import commands
import gspread
from oauth2client.crypt import AppIdentityError
from oauth2client.service_account import ServiceAccountCredentials
from urllib.request import urlopen as uReq
import asyncio
import ast
from bs4 import BeautifulSoup as soup
from six import string_types
from Bot_Classes import *
import platform
import random as rd
import Rpi_db as db

def Correct_path():
    myos = platform.system()

    if myos == 'Windows':
        mypath = None
    elif myos == "Linux":
        mypath = '/home/kingbubiii/Documents/discordbotgamelib/'

    return mypath

#things to get setup with google, being authorized and whatnot
scope = [
    "https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

#credentials in list
mypath = Correct_path()
if mypath == None:
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
else:
    creds = ServiceAccountCredentials.from_json_keyfile_name(mypath + "creds.json", scope)

#passes in all credentials to make sure changes/ viewing are allowed
sheets_client = gspread.authorize(creds)

# Open the spreadhseet
wb = sheets_client.open('discord_bot_data')

#discord bot token needed to run bot
if mypath == None:
    TOKEN = str(open("token.txt").read())
else:
    TOKEN = str(open(mypath + "token.txt").read())

#creating client instance and identifying prefix for commands 
prefix = '>>'
intents = discord.Intents.default()
intents.members = True

discord_client = commands.Bot(command_prefix=prefix, intents=intents)
#discord_client.case_insensitive = True
#removing default help command
discord_client.remove_command('help')

# allows users to search libraries, their own or others, for game names
async def Search_func(ctx, search_query, user_query=None, called_from=False):
    #open worksheet
    wks = wb.get_worksheet(0)

    #get entire worksheet in one variable
    wks_list = wks.get_all_values()

    results_data = []
    #iterates though entire sheet by row
    for game in wks_list:
        #default user to search for in command author
        if user_query == None:
            #checks if game row member name matches with command author 
            if ctx.author.mention == game[0]:
                #checks if game name query match any part of current row game name
                if search_query == None or search_query in game[1].lower():
                    #add current row data to results array
                    results_data.append(game[1])
        else:
            #checks if game row member name matches with user query name
            if user_query == game[0]:
                #checks if game name query match any part of current row game name
                if search_query == None or search_query in game[1].lower():
                    #add current row data to results array
                    results_data.append(game[1])

    #creates a new library from results list 
    results_lib = Library(User="results",data=results_data)

    #creates embed from result class
    await array_to_embed(results_lib)

    #send first page of results embed back to member
    response = await ctx.send(embed=results_lib.CurrentPage())
    #reacts with navigation emojis and database modification emojis if applicable
    await results_lib.React(response,called_from)
    
    #function for when a member reacts
    @discord_client.event
    async def on_reaction_add(reaction, user):
        #checks if the member is not the bot itself
        #prevents looping on itself
        if user != discord_client.user:

            #temparary variable
            reaction_num = None

            #gets reaction index
            for count, item in enumerate(results_lib.DownloadReacts):
                if reaction.emoji == item:
                    reaction_num = count
            
            #doesn't interat with database if member is just changing pages
            if not reaction_num == None:
                #select game for memeber to change personal data
                game_name = results_lib.data_array[reaction_num + (5*results_lib.PageNumber)]

                #iterates through entire database one row at a time 
                for row, row_game_name in enumerate(wks.col_values(2)):

                    #looking for selected game row
                    if game_name == row_game_name:
                        #checks if reaction author and library owner match
                        if wks.cell(row+1,1).value == user.mention:
                            #init state value 
                            state = ''
                            #determines output message and database value
                            if called_from == 'Download':
                                state = 'Yes'
                            elif called_from == 'Uninstall':
                                state = 'No'
                                #updates proper cell
                            wks.update_cell(row+1,7,state)
                            #send message to member that database has been updated
                            await ctx.send("```" + game_name + " has been marked as {0}downloaded```".format("" if state == "Yes" else "not "))
                            #exits loop
                            break
            
            #if forward emoji
            if reaction.emoji == results_lib.NavigationReacts[1]:
                #delete last embed
                await reaction.message.delete()
                #increment current page
                results_lib.NextPage()
                #resend current page
                response = await ctx.send(embed=results_lib.CurrentPage())
                #send apprioprate reactions again
                await results_lib.React(response,called_from)
            #if backward emoji
            if reaction.emoji == results_lib.NavigationReacts[0]:
                #delete last embed
                await reaction.message.delete()
                #decrement current page
                results_lib.PreviousPage()
                #resend current page
                response = await ctx.send(embed=results_lib.CurrentPage())
                #send apprioprate reactions again
                await results_lib.React(response,called_from)
    #send result embed
    return response

# accesses the database to recall info on games to create a library class
async def sheet_data_to_array(libclass, formatting=None):
    #open first sheet
    wks = wb.get_worksheet(0)
    #gets the whole game data worksheet as a single variable to be accessable with one read 
    current_sheet = wks.get_all_values()
    #gets the number of games the user has for the program to know when to stop looking for more games
    num_of_games = len(wks.findall(libclass.User))


    #defaults to just the downloaded format option 
    if formatting == None:
        #looks at each row of the whole sheet individually
        for row in current_sheet:
            #skips the very first row of the sheet to skip the row headers
            if not row == current_sheet[0]:
                #creates an instance of the game class to make information more readable and accessable
                item = Game(row)
                #makes sure the owner of the current game instace is the user that was specified in the command
                if item.Owner == libclass.User:
                    #adds a field per game to the embed with the downloaded status
                    libclass.data_array.append((item.FullName,'Downloaded: ' + item.Downloaded))

    elif formatting[0] == '-':
        validQuery = True
        
        for char in formatting[1::]:
            if not char in ['f','n','a','h','s','o','d','i']:
                return False

        if validQuery == True:
            for row in current_sheet:
                if not row == current_sheet[0]:
                    item = Game(row)
                    if item.Owner == libclass.User:
                        game_details = item.Format_Details(formatting)
                        libclass.data_array.append((game_details[0],game_details[1]))

# formats serveral pages of embeds using the format details specified by user
async def array_to_embed(libclass):
    if type(libclass.data_array[0]) == list or type(libclass.data_array[0]) == tuple:
        for count, game in enumerate(libclass.data_array):
            #adds a field per game to the embed with the downloaded status
            libclass.Page.add_field(name=game[0], value=game[1], inline=False)
            # checks to make sure there is only 5 games per page of the library so it doesnt get overwhelming and the embed cant hold the whole library
            if (count%libclass.MaxGamesOnPage == 0 and count > 0) or count - len(libclass.data_array) == 0:
                libclass.AddPage()
    elif type(libclass.data_array[0]) == str:
        for count, game in enumerate(libclass.data_array):
            #adds a field per game to the embed with the downloaded status
            libclass.Page.add_field(name=game, value="Mark as downloaded by react with 5" if (count+1)%libclass.MaxGamesOnPage == 0 else "Mark as downloaded by react with " + str((count+1)%libclass.MaxGamesOnPage), inline=False)
            if (((count+1)%libclass.MaxGamesOnPage) == 0 and count > 0) or count - len(libclass.data_array) == 0:
                libclass.AddPage()
    #if there are 5 or less items
    if len(libclass.Embeds) == 0:
        libclass.AddPage()

#allows command function arguements to be called from anywhere when using a command
async def Arg_Assign(all_args):

    # filters down entire list of arguments down to ones with member character tags '<@!'
    # converts from tuple to list
    members = list(filter(lambda arg: "<@" in arg , all_args))
    
    # checks if there is a format choice or not
    #if no
    if len(members) == len(all_args):
        #format becomes none type
        formatting = None
    #if yes
    else:
        #make format a list of all the arguments
        formatting = list(all_args)

        #remove all member arguemnts so formatting is left alone
        for member in members:
            formatting.remove(member)
        #format becomes string from list
        formatting = formatting[0]
    
    #if only one member is mentioned convert it to a string instead of leaving it in an array
    if len(members) == 1:
        members = members[0]

    return members, formatting


# a function to show similarities between members libraries
# can compare two or more members at a time
async def compare_func(formatting, *members):

    #creating empty arrays to appaend data later
    peoples_libs = []
    peoples_games = []

    #loop through each mentioned person to create a library class for each
    for count, person in enumerate(members[0]):
        peoples_libs.append(Library(person))
        if await sheet_data_to_array(peoples_libs[count], formatting) == False:
            return "```Selected formatting is not an option```"
        else:
            temp = [item[0] for item in peoples_libs[count].data_array]
            peoples_games.append(temp)

    for count, games in enumerate(peoples_games):
        peoples_games[count] = set(games)

    common_games = set(peoples_games[0])
    for count in range(len(peoples_games)-1):
        common_games = common_games.intersection(set(peoples_games[count+1]))
    common_games = list(common_games)

    games_with_embed_data = []

    for count in range(len(common_games)):
        temp = [common_games[count],""]

        for person in peoples_libs:
            for item in person.data_array:
                if common_games[count] == item[0]:
                    temp[1] += item[1] + "\n"
        games_with_embed_data.append(temp)
    Common_lib = Library(User = "Common Games",data= games_with_embed_data)
    await array_to_embed(Common_lib)
    return Common_lib

async def get_user_class(member_id_str):
    member_class = discord_client.get_user(int(member_id_str.replace('<@','').replace('>','')))
    return member_class

#signaling the bot is online and ready to be used
#Setting the help command to be what the bot is "playing"
@discord_client.event
async def on_ready():
    print('Ready set let\'s go')
    await discord_client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=prefix + "help"))

@discord_client.command()
async def compare(ctx, *all_args):

    members, formatting = await Arg_Assign(all_args)
    
    Common_lib = await compare_func(formatting, members)

    response = await ctx.send(embed=Common_lib.CurrentPage())
    await Common_lib.React(response,False)

    @discord_client.event
    async def on_reaction_add(reaction, user):
        if user != discord_client.user:
            
            if reaction.emoji == Common_lib.NavigationReacts[1]:
                await reaction.message.delete()
                Common_lib.NextPage()

            if reaction.emoji == Common_lib.NavigationReacts[0]:
                await reaction.message.delete()
                Common_lib.PreviousPage()
                
            response = await ctx.send(embed=Common_lib.CurrentPage())
            await Common_lib.React(response,False)

#member command to update database games as downloaded
@discord_client.command()
async def download(ctx, download_query=None, user_query=None):
    #calls search command with 'Download' perameter
    results = await search(ctx, download_query, user_query, called_from='Download')

# A simple command that repeats what was sent
# mainly useful for debugging 
@discord_client.command() 
async def echo(ctx, *, msg='echo'):
    #await ctx.send(f"""```{ctx.author.id}: {msg}```""")
    #await ctx.send(f"""```{ctx.guild}```""")
    await ctx.send(f"""```{msg}```""")

# teaches members how to use bot
# you can specify commands to get in depth help on them
@discord_client.command()
async def help(ctx, commandName=None):
    helpEmbed = discord.Embed(title = 'basic bitch', color = discord.Color.orange())

    if commandName == None:
        helpEmbed.title = 'List of short command descriptions'
        helpEmbed.add_field(name = 'Command Prefix: ', value =  'put this, "' + prefix + '", in front of specified command name to be able to call the command', inline=False)
        helpEmbed.add_field(name = 'compare', value = 'Shows common games between all mentioned people in pagified version like reading a library', inline=False)
        helpEmbed.add_field(name = 'download', value = 'Page through library to select what games are downloaded locally on your pc', inline=False)
        helpEmbed.add_field(name = 'echo', value = 'Repeats what you say in a fancy code block', inline=False)
        helpEmbed.add_field(name = 'help', value = 'One optional arguement: commandName\nSpecify a command\'s name to get more details on that command', inline=False)
        helpEmbed.add_field(name = 'readlib', value = 'Allows you and others to read the games you have installed.', inline=False)
        helpEmbed.add_field(name = 'search', value = 'Returns list of games in anyone\'s library that matches your search term', inline=False)
        helpEmbed.add_field(name = 'steamid', value = 'Either creates new profile for member or updates exsisting Steam ID number', inline=False)
        #helpEmbed.add_field(name = 'download', value = '', inline=False)


    elif commandName == 'echo':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = commandName, value = 'Repeats what you say in a fancy code block\n\n\
                                                        Optional command(s): message\n\n\
                                                        Default message to \'echo\'\n\n\
                                                        The arguement can be as long as you want including spaces\n\n \
                                                        Default Example: >>echo\nDefault Ouptut: echo\n\n\
                                                        Filled argument Example: >>echo This command is useless \n\
                                                        Filled arguement Output: This command is useless')
        helpEmbed.add_field(name = 'Examples', value = '>>echo testing testing')

    elif commandName == 'readlib':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = commandName, value = 'Mention a person to read their library\n\n\
                                                        Manditory command(s): username\nOptional command(s): formatting\n\n\
                                                        Specify formatting by a \'-\' then put any combination of the letters\
                                                        \'a\' \'h\' \'s\' \'o\' \'d\'\n\n\
                                                        \'a\' (All): It will display all avaiable info options\n\
                                                        \'h\' (Hours): Displays the number of hours you\'ve put into the game\n\
                                                        \'s\' (Link): Gives game\'s Steam link\n\
                                                        \'o\' (Online): Displays if the game is multiplayer\n\
                                                        \'d\' (Downloaded): Displays if you have the game downloaded')

        helpEmbed.add_field(name = 'Examples', value = '>>readlib @KingBubIII\n\n\
                                                        >>readlib @KingBubIII -a\n\n\
                                                        >>readlib @KingBubIII -hd\n\n\
                                                        >>readlib @KingBubIII -dhos\n\n')

    elif commandName == 'compare':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = commandName, value = 'See all games each mentioned person has in common\n\
                                                        Can also show details using the details option of readlib')
        helpEmbed.add_field(name = 'Examples', value = '>>compare @KingBubIII @Test123\n\n\
                                                        >>compare @KingBubIII   @Test123 -d\n\
                                                        Shows common games that are downloaded\n\n\
                                                        >>compare @KingBubIII @Test123 -hso\n\
                                                        Shows common games while showing hours, Steam link, and if its multiplayer for each player')

    elif commandName == 'download':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = commandName, value = 'This function allows you to mark games as downloaded in my database\n\n\
                                                        The output is the same as a readlib command but with numbered reaction options\n\n\
                                                        Reacting with a numbered reaction will mark that game on the current page as downloaded\n\n\
                                                        You are the only one that can mark games as downloaded in your library\n\n')
        helpEmbed.add_field(name = 'Examples', value = '>>download')

    elif commandName == 'steamid':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = commandName, value = 'Update your steam ID in my database\n\n\
                                                            If you\'re new I\'ll create a new profile in my database and add your ID\n\n\
                                                            Your steam ID directs me to your Steam profile\n\n\
                                                            Make sure you set your acount to public though!')
        helpEmbed.add_field(name = 'Examples', value = '>>steamid 76561198286078396\n\n\
                                                        >>steamid 12345678912345678')

    elif commandName == 'search':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = commandName, value = 'Just a basic search function\n\n\
                                                        The default library to search if you don\'t mention a person is your own\n\n\
                                                        Be as specific or as general as you would like\n\n\
                                                        Can only search one person\'s library at a time\n\n')
        helpEmbed.add_field(name = 'Examples', value = '>>search ba @KingBubIII\n\n\
                                                        >>search ba')

    #elif commandName == '':
        #helpEmbed.title = 'In depth help for'
        #helpEmbed.add_field(name = commandName, value = 'explain')
        #helpEmbed.add_field(name = 'Examples', value = 'stuff')

    await ctx.send(embed=helpEmbed)

# sends a discord embed that users can page through to view all games and details in database
# anyone can call to read another persons library
@discord_client.command()
async def readlib(ctx, *all_args):

    member, formatting = await Arg_Assign(all_args)

    UsersLibrary = Library(User=member)
    
    #sort sheet by game names ascending if they don't ask about hours
    wks.sort((2, 'asc'))

    if not formatting == None:
        #sort sheet by number of hours descending if they ask about hours
        if 'h' in formatting:
            wks.sort((3, 'des'))

    if await sheet_data_to_array(UsersLibrary, formatting) == False:
        await ctx.send("```Selected formatting is not an option```")
    else:

        await array_to_embed(UsersLibrary)
        
        response = await ctx.send(embed=UsersLibrary.CurrentPage())
        await UsersLibrary.React(response,False)

        @discord_client.event
        async def on_reaction_add(reaction, user):
            if user != discord_client.user:
                
                if reaction.emoji == UsersLibrary.NavigationReacts[1]:
                    await reaction.message.delete()
                    UsersLibrary.NextPage()

                if reaction.emoji == UsersLibrary.NavigationReacts[0]:
                    await reaction.message.delete()
                    UsersLibrary.PreviousPage()
                    
                response = await ctx.send(embed=UsersLibrary.CurrentPage())
                await UsersLibrary.React(response,False)

# runs the Search_func command
@discord_client.command()
async def search(ctx, search_query, user_query=None,called_from=False):
    #runs search command without being intention to change database values 
    response = await Search_func(ctx, search_query, user_query, called_from)

@discord_client.command()
async def steamid(ctx, input_id):
    #takes discord user mention and formats it to where its useable
    member_name = str(ctx.author.mention)
    
    #open steam profile info sheet
    wks = wb.get_worksheet(1)

    #gets all member ids that are on record
    usernames_list = wks.col_values(1)
    #await ctx.send(usernames_list)

    #checks if mentioned member is on record
    if member_name in usernames_list:
        #finds the row the member record is on
        username_row = usernames_list.index(member_name) + 1
        #updates cell value with new id
        wks.update_cell(username_row, 2, input_id)
        #sends confirmation message back into channel 
        await ctx.send('```Your information has been updated```')

    else:
        # creates an array with new memeber record info
        new_user_info = [member_name,input_id, "https://steamcommunity.com/profiles/"+input_id, "https://steamcommunity.com/profiles/" + input_id + "/games/?tab=all"]
        #creates new row in database
        wks.append_row(new_user_info, 'RAW')
        #sends confirmation message back into channel
        await ctx.send('```New infomation added```')

# a background function to update the database
# updates hours played per game and adds new games purchased
# function only updates one member's library
@discord_client.command()
async def _update_lib(ctx, member_name):
    
    #member_name = ctx.author.mention
    # opens sheet that contains info for steam library access
    wks = wb.get_worksheet(1)

    #gets all members names
    usernames_list = wks.col_values(1)

    # runs if memeber has steam info inputted
    if member_name in usernames_list:
        #url to scrap as a varible
        steam_lib_link = wks.cell(usernames_list.index(member_name)+1,4,'FORMATTED_VALUE').value
        
        #opens connection to client website and downloads information
        uClient = uReq(steam_lib_link)

        #mloads html content into variable
        page_html = uClient.read()
        #closes connection to client website
        uClient.close()

        #parse the html document, making soup object
        page_soup = soup(page_html, "html.parser")

        #getting all game containers list
        json_script = page_soup.find_all("script",{"language":"javascript"})

        #editting data as a string to be convertable to a dictionary
        all_game_info = json_script[0].next.split(';')[0]
        all_game_info = all_game_info[len("  			var rgGames = ["):-1]
        all_game_info = all_game_info.replace("},{", "},,{")
        all_game_info = all_game_info.replace('\\','')
        all_game_info = all_game_info.replace('false','False')
        all_game_info = all_game_info.replace('true','True')
        undicted_game_info = list(all_game_info.split(",,"))
        #sets game info sheet to active
        wks = wb.get_worksheet(0)
        
        #gets the current sheet to be compared to tell if new games needed to be added
        current_sheet = wks.get_all_values()

        for game in undicted_game_info:
            #makes dictionary for game to easily access information
            game_info_dict = ast.literal_eval(game)
            if 'hours_forever' in game_info_dict:
                useful_game_info = [member_name, game_info_dict['name'], game_info_dict['hours_forever'], game_info_dict['appid'], 'https://store.steampowered.com/app/'+str(game_info_dict['appid']), 'No', 'No', 'none',]

                steam_lib_link = useful_game_info[4]
            
                #opens connection to client website and downloads information
                uClient = uReq(steam_lib_link)

                #mloads html content into variable
                page_html = uClient.read()
                #closes connection to client website
                uClient.close()

                #parse the html document, making soup object
                page_soup = soup(page_html, "html.parser")

                json_script = page_soup.find_all("a", class_="app_tag")
                tags = []
                for index in range(len(json_script)):
                    tag = json_script[index].next.replace('\n', '').replace('\r', '').replace('\t', '')
                    tags.append(tag)
                    db_multiplayer = False
                    if tag == "Multiplayer":
                        useful_game_info[5] = "Yes"
                        db_multiplayer = True
                #loops through each row in the games sheet to update and add new games to sheet
                row_count = 1
                
                #updates Rpi database
                member_class = await get_user_class(member_name)
                db.update_db(ctx.guild.name, member_class.name ,game_info_dict,', '.join(tags), db_multiplayer)
            #await ctx.send("```I do not have a Steam ID for you, please go input one with the 'steamid' command```")
            
        await ctx.send("```Your library has been updated```")

# will give a common game suggestion between all mentioned members
@discord_client.command()
async def random(ctx, *members):
    #get a result class
    result = await compare_func('-d', members)

    #empty list init
    common_downloaded = []

    #iterate through list one game at a time
    for item in result.data_array:
        #checks if both people have the game downloaded
        if 'Yes\n'*len(members) == item[1].replace('Downloaded: ', ''):
            #add to temparary list to choose from later
            common_downloaded.append(item)
    
    #select random element in the list, therefore random game
    random_game = rd.choice(common_downloaded)
    #create new embed variable
    single_embed = discord.Embed(title = "Random Game", description = 'Choices are from downloaded only games' , color = discord.Color.blue())
    #add field with chosen game name
    single_embed.add_field(name = 'Random Game: ', value = random_game[0] , inline=False)
    #send chosen game embed
    await ctx.send(embed=single_embed)

@discord_client.command()
async def uninstall(ctx, game_query=None, user_query=None):
    results = await search(ctx, game_query, user_query, called_from='Uninstall')

#discord_client.loop.create_task(update_libs())
discord_client.run(TOKEN)