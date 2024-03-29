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

#things to get setup with google, being authorized and whatnot
scope = [
    "https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

#credentials in list
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

#passes in all credentials to make sure changes/ viewing are allowed
sheets_client = gspread.authorize(creds)

# Open the spreadhseet
wb = sheets_client.open('discord_bot_data')

#discord bot token needed to run bot
TOKEN = str(open("token.txt").read())

#creating client instance and identifying prefix for commands 
prefix = '>>'
discord_client = commands.Bot(command_prefix=prefix)
#discord_client.case_insensitive = True
#removing default help command
discord_client.remove_command('help')

async def Search_func(ctx, search_query, user_query=None, download__func=False):
    wks = wb.get_worksheet(0)

    wks_list = wks.get_all_values()

    results_data = []
    for game in wks_list:
        #print(ctx.author.mention)
        if user_query == None:
            if ctx.author.mention.replace("!","") == game[0]:
                    if search_query == None or search_query in game[1].lower():
                        results_data.append(game[1])
        else:
            if user_query.replace("!","") == game[0]:
                if search_query == None or search_query in game[1].lower():
                    results_data.append(game[1])

    #print(results_data)
    results_lib = Library(User="results",data=results_data)

    await array_to_embed(results_lib)

    response = await ctx.send(embed=results_lib.CurrentPage())
    await results_lib.React(response,download__func)
    
    @discord_client.event
    async def on_reaction_add(reaction, user):
        if user != discord_client.user:
            if download__func == True:
                if reaction.emoji == results_lib.DownloadReacts[0]:
                    game_name = results_lib.data_array[0 + (5*results_lib.PageNumber)]

                    for row, row_game_name in enumerate(wks.col_values(2)):
                        if game_name == row_game_name:
                            if wks.cell(row+1,1).value == user.mention:
                                wks.update_cell(row+1,7,"Yes")
                                await ctx.send("```" + game_name + " has been marked as downloaded```")
                                break
                
                if reaction.emoji == results_lib.DownloadReacts[1]:
                    game_name = results_lib.data_array[1 + (5*results_lib.PageNumber)]
                    for row, row_game_name in enumerate(wks.col_values(2)):
                        if game_name == row_game_name:
                            if wks.cell(row+1,1).value == user.mention:
                                wks.update_cell(row+1,7,"Yes")
                                await ctx.send("```" + game_name + " has been marked as downloaded```")
                                break

                if reaction.emoji == results_lib.DownloadReacts[2]:
                    game_name = results_lib.data_array[2 + (5*results_lib.PageNumber)]
                    for row, row_game_name in enumerate(wks.col_values(2)):
                        if game_name == row_game_name:
                            if wks.cell(row+1,1).value == user.mention:
                                wks.update_cell(row+1,7,"Yes")
                                await ctx.send("```" + game_name + " has been marked as downloaded```")
                                break

                if reaction.emoji == results_lib.DownloadReacts[3]:
                    game_name = results_lib.data_array[3 + (5*results_lib.PageNumber)]
                    for row, row_game_name in enumerate(wks.col_values(2)):
                        if game_name == row_game_name:
                            if wks.cell(row+1,1).value == user.mention:
                                wks.update_cell(row+1,7,"Yes")
                                await ctx.send("```" + game_name + " has been marked as downloaded```")
                                break

                if reaction.emoji == results_lib.DownloadReacts[4]:
                    game_name = results_lib.data_array[4 + (5*results_lib.PageNumber)]

                    for row, row_game_name in enumerate(wks.col_values(2)):
                        if game_name == row_game_name:
                            if wks.cell(row+1,1).value == user.mention:
                                wks.update_cell(row+1,7,"Yes")
                                await ctx.send("```" + game_name + " has been marked as downloaded```")
                                break

            if reaction.emoji == results_lib.InitialReacts[1]:
                await reaction.message.delete()
                results_lib.NextPage()
                response = await ctx.send(embed=results_lib.CurrentPage())
                await results_lib.React(response,download__func)

            if reaction.emoji == results_lib.InitialReacts[0]:
                await reaction.message.delete()
                results_lib.PreviousPage()
                response = await ctx.send(embed=results_lib.CurrentPage())
                await results_lib.React(response,download__func)

    return response

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

    #print(libclass.data_array)

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

#Setting the help command to be what the bot is playing 
@discord_client.event
async def on_ready():
    print('Ready set let\'s go')
    await discord_client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=prefix + "help"))

@discord_client.command()
async def compare(ctx, person1, person2, formatting=None):
    person1_lib = Library(person1)
    person2_lib = Library(person2)

    if await sheet_data_to_array(person1_lib, formatting) == False or await sheet_data_to_array(person2_lib, formatting) == False:
        await ctx.send("```Selected formatting is not an option```")
    else:
        person1_games = [item[0] for item in person1_lib.data_array]
        person2_games = [item[0] for item in person2_lib.data_array]

        common_games = list(set(person1_games).intersection(person2_games))

        games_with_embed_data = []

        for count in range(len(common_games)):
            temp = [common_games[count],""]
            for item in person1_lib.data_array:
                if common_games[count] == item[0]:
                    temp[1] += item[1] + "\n"

            for item in person2_lib.data_array:
                if common_games[count] == item[0]:
                    temp[1] += item[1] + "\n"
            games_with_embed_data.append(temp)
        
        #print(games_with_embed_data)
        Common_lib = Library(User = "Common Games",data= games_with_embed_data)
        
        await array_to_embed(Common_lib)
                                
        response = await ctx.send(embed=Common_lib.CurrentPage())
        await Common_lib.React(response,False)

        @discord_client.event
        async def on_reaction_add(reaction, user):
            if user != discord_client.user:
                
                if reaction.emoji == Common_lib.InitialReacts[1]:
                    await reaction.message.delete()
                    Common_lib.NextPage()

                if reaction.emoji == Common_lib.InitialReacts[0]:
                    await reaction.message.delete()
                    Common_lib.PreviousPage()
                    
                response = await ctx.send(embed=Common_lib.CurrentPage())
                await Common_lib.React(response,False)

@discord_client.command()
async def download(ctx, download_query=None, user_query=None):
    wks = wb.get_worksheet(0) #open first sheet

    try: 
        download_query = int(download_query)
        
        #gets the row with game ids
        id_list =  wks.col_values(4)

        if download_query in id_list:
            for row, id in enumerate(id_list):
                if id == download_query:
                    if ctx.author.mention == wks.cell(row+1,1).value:
                        wks.update_cell(row+1,7,"Yes")
                        game_name = wks.cell(row+1,2).value
                        await ctx.send("```You have downloaded " + game_name + " ```")
        else:
            await ctx.send("```That ID does not match any game ID's I have```")
        

    except (ValueError, TypeError) as e:
        results = await search(ctx, download_query, user_query, called_from_download=True)

@discord_client.command() 
async def echo(ctx, *, msg='echo'):
    await ctx.send(f"""```{msg}```""")

@discord_client.command()
async def help(ctx, commandName=None):

    if commandName == None:
        helpEmbed = discord.Embed(title = 'List of short command descriptions', color = discord.Color.orange())
        helpEmbed.add_field(name = 'Command Prefix: ', value =  'put this, "' + prefix + '", in front of specified command name to be able to call the command', inline=False)
        helpEmbed.add_field(name = 'help', value = 'One optional arguement: commandName\nSpecify a command\'s name to get more details on that command', inline=False)
        helpEmbed.add_field(name = 'echo', value = 'Repeats what you say in a fancy code block', inline=False)
        helpEmbed.add_field(name = 'readlib', value = 'Allows you and others to read the games you have installed.', inline=False)
        helpEmbed.add_field(name = 'steamid', value = 'Either creates new profile for member or updates exsisting Steam ID number', inline=False)


    elif commandName == 'echo':
        helpEmbed = discord.Embed(title = 'In depth help for ', color = discord.Color.orange())
        helpEmbed.add_field(name = commandName, value = 'Repeats what you say in a fancy code block\n\n\
                                                        One optional arguement: message\n\n\
                                                        If the arguement is not filled then the message defaults to \'echo\'\n\n\
                                                        The arguement can be as long as you want including spaces\n\n \
                                                        Default Example: >>echo\nDefault Ouptut: echo\n\n\
                                                        Filled argument Example: >>echo This command is useless \n\
                                                        Filled arguement Output: This command is useless')

    elif commandName == 'readlib':
        helpEmbed = discord.Embed(title = 'In depth help for ', color = discord.Color.orange())
        helpEmbed.add_field(name = commandName, value = 'Allows you and others to read the games you have installed.\n\n\
                                                        This command has one manditory command: username and one optional command: formatting\n\
                                                        Specify your username or another person\'s in the server to read the users library of games\n\
                                                        The formatting command allows your to read more or less details of the library of the user you specify. \
                                                        To do this you must put a \'-\' then put any number of and combination of the letters  \
                                                        \'f\' \'n\' \'a\' \'h\' \'s\' \'o\' \'d\'.\n\
                                                        \'f\': Displays full game\'s name\n\
                                                        \'n\': Displays game\'s nickname \n\
                                                        \'a\': stands for all; It will display all avaiable info options \n\
                                                        \'h\': stands for hours; Displays the number of hours you\'ve put into the game \n\
                                                        \'s\': stands for link; Displays the game\'s Steam link \n\
                                                        \'o\': stands for online; Displays weather or not the game is multiplayer \n\
                                                        \'d\': stands for downloaded; Displays weather or not you have told me you have the game downloaded')

    await ctx.send(embed=helpEmbed)

@discord_client.command()
async def readlib(ctx, user_mention, formatting=None):
    UsersLibrary = Library(User=user_mention)

    if await sheet_data_to_array(UsersLibrary, formatting) == False:
        await ctx.send("```Selected formatting is not an option```")
    else:

        await array_to_embed(UsersLibrary)
        
        #print(UsersLibrary.PageNumber)
        response = await ctx.send(embed=UsersLibrary.CurrentPage())
        await UsersLibrary.React(response,False)

        @discord_client.event
        async def on_reaction_add(reaction, user):
            if user != discord_client.user:
                
                if reaction.emoji == UsersLibrary.InitialReacts[1]:
                    await reaction.message.delete()
                    UsersLibrary.NextPage()

                if reaction.emoji == UsersLibrary.InitialReacts[0]:
                    await reaction.message.delete()
                    UsersLibrary.PreviousPage()
                    
                response = await ctx.send(embed=UsersLibrary.CurrentPage())
                await UsersLibrary.React(response,False)
    
@discord_client.command()
async def search(ctx, search_query, user_query=None,called_from_download=False):
    response = await Search_func(ctx, search_query, user_query, called_from_download)

@discord_client.command()
async def steamid(ctx, input_id):
    member_name = ctx.author.mention
    member_name = str(member_name).replace("!","")
    #await ctx.send(member_name)
    wks = wb.get_worksheet(1) #open second sheet

    usernames_list = wks.col_values(1)
    #await ctx.send(usernames_list)

    if member_name in usernames_list:
        username_row = usernames_list.index(member_name) + 1
        wks.update_cell(username_row, 2, input_id)
        await ctx.send('```Your information has been updated```')

    else:
        new_user_info = [member_name,input_id, "https://steamcommunity.com/profiles/"+input_id, "https://steamcommunity.com/profiles/" + input_id + "/games/?tab=all"]
        wks.append_row(new_user_info, 'RAW')
        await ctx.send('```New infomation added```')
                
@discord_client.command()
async def update_lib(ctx, member_name):
    
    member_name = str(member_name).replace("!","")
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
                
                for index in range(len(json_script)):
                    tag = json_script[index].next.replace('\n', ' ').replace('\r', '').replace('\t', '').replace(' ', '')
                    if tag == "Multiplayer":
                        useful_game_info[5] = "Yes"
                        break
                #loops through each row in the games sheet to update and add new games to sheet
                row_count = 1
                
                for row in current_sheet:
                    if row[:2] == useful_game_info[:2]:
                        wks.update_cell(row_count, 3, useful_game_info[2])
                    row_count+=1
                for row in current_sheet:
                    del row[2:]
                    row = list(set(row))
                if not useful_game_info[:2] in current_sheet:
                    wks.append_row(useful_game_info,'RAW')
            #await ctx.send("```I do not have a Steam ID for you, please go input one with the 'steamid' command```")
            
        await ctx.send("```Your library has been updated```")

#discord_client.loop.create_task(update_libs())
discord_client.run(TOKEN)