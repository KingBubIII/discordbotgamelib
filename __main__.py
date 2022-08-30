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
    if user_query == None:
        member = ctx.author
    else:
        member = await get_user_class(user_query)
    results_data = db.search(ctx.guild, member.name, search_query)
    #print(results_data)
    if len(results_data) == 0:
        await ctx.send('```I found no matches```')
        return False
    #creates a new library from results list 
    results_lib = Library(User="results",data=results_data)

    #creates embed from result class
    await create_embeds(results_lib, None)

    #send first page of results embed back to member
    response = await ctx.send(embed=results_lib.CurrentPage())
    #reacts with navigation emojis and database modification emojis if applicable
    await results_lib.React(response,called_from)
    #send result embed
    return response, results_lib

# formats serveral pages of embeds using the format details specified by user
async def create_embeds(libclass, members):
    if type(libclass.data_array[0]) == list or type(libclass.data_array[0]) == tuple:
        for count, game in enumerate(libclass.data_array):
            
            if type(libclass.data_array[0][1]) == str:
                #adds a field per game to the embed with the downloaded status
                libclass.Page.add_field(name=game[0], value=game[1], inline=False)
            
            elif type(libclass.data_array[0][1]) == list:
                formatted = ""
                details_len = len(game[1][0].split('\n'))
                
                for index in range(0,len(members), 2):
                    grouped_people = 1 if index+1 == len(members) else 2

                    for shift in range(grouped_people):
                        temp_str = '**' + members[index+shift] + '**'
                        temp_str = temp_str.center(32, '\u200b')
                        temp_str = temp_str.replace('\u200b',' \u200b')
                        formatted += temp_str

                    formatted += '\n\u200b'

                    for i in range(details_len):
                        for shift in range(grouped_people):
                            temp_str = game[1][index+shift].split('\n')[i]
                            temp_str = temp_str.center(32, '\u200b')
                            temp_str = temp_str.replace('\u200b',' \u200b')
                            formatted += temp_str
                            if shift+1 == grouped_people and (index+1 != len(members) or i+1 != details_len):
                                formatted += '\n\u200b'

                #print(len(formatted))
                libclass.Page.add_field(name=game[0], value=formatted, inline=False)
            
            # checks to make sure there is only 5 games per page of the library so it doesnt get overwhelming and the embed cant hold the whole library
            if (((count+1)%libclass.MaxGamesOnPage) == 0 and count > 0) or count - len(libclass.data_array) == 0:
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
        misc = None
    #if yes
    else:
        #make format a list of all the arguments
        misc = list(all_args)

        #remove all member arguemnts so misc is left alone
        for member in members:
            misc.remove(member)
        #format becomes string from list
        misc = misc[0]
    
    #if only one member is mentioned convert it to a string instead of leaving it in an array
    if len(members) == 1:
        members = members[0]
    elif len(members) == 0:
        members = None

    return members, misc


# a function to show similarities between members libraries
# can compare two or more members at a time
async def compare_func(ctx, formatting, members):

    #creating empty arrays to appaend data later
    peoples_libs = []
    peoples_games = []

    Common_lib = Library(User = "Common Games")
    db.compare(ctx.guild, members, Common_lib, formatting)
    await create_embeds(Common_lib, members)
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

    for count in range(len(members)):
        user_class = await get_user_class(members[count])
        members[count] = user_class.name

    Common_lib = await compare_func(ctx, formatting, members)

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
async def download(ctx, download_query=None):
    member = await get_user_class(ctx.author.mention)
    #calls search command with 'Download' perameter
    results, results_lib = await Search_func(ctx, download_query, None, called_from='Download')
    
    @discord_client.event
    async def on_reaction_add(reaction, user):
        if user != discord_client.user:
            
            if reaction.emoji in results_lib.NavigationReacts:
                await reaction.message.delete()
                if reaction.emoji == results_lib.NavigationReacts[0]:
                    results_lib.PreviousPage()
                elif reaction.emoji == results_lib.NavigationReacts[1]:
                    results_lib.NextPage()

                response = await ctx.send(embed=results_lib.CurrentPage())
                await results_lib.React(response,'Download')

            if reaction.emoji in results_lib.DownloadReacts:
                game_num = results_lib.PageNumber * results_lib.MaxGamesOnPage + results_lib.DownloadReacts.index(reaction.emoji)
                download_query = results_lib.data_array[game_num][2]
                name = results_lib.data_array[game_num][0]
                db.mark_as(ctx.guild, member.name, download_query, True)
                await ctx.send('```{0} has been marked as downloaded```'.format(name))

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
    if member == None:
        member = await get_user_class(ctx.author.mention)
    else:
        member = await get_user_class(member)
    UsersLibrary = Library(User=member.name)

    db.readlib(ctx.guild, UsersLibrary, formatting)
    await create_embeds(UsersLibrary, None)
    
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
async def search(ctx, *args):
    user_query=None
    search_query=None
    user_query, search_query = await Arg_Assign(args)
    if search_query == None:
        await ctx.send('```You did not specify what to search with. Try again```')
        return
    #runs search command without being intention to change database values 
    response, response_lib = await Search_func(ctx, search_query, user_query, False)

    @discord_client.event
    async def on_reaction_add(reaction, user):
        if user != discord_client.user:
            
            if reaction.emoji == response_lib.NavigationReacts[1]:
                await reaction.message.delete()
                response_lib.NextPage()

            if reaction.emoji == response_lib.NavigationReacts[0]:
                await reaction.message.delete()
                response_lib.PreviousPage()
                
            response = await ctx.send(embed=response_lib.CurrentPage())
            await response_lib.React(response,False)

@discord_client.command()
async def steamid(ctx, steamID):
    #updates mysql database and returns boolean value
    new_profile = db.profile_update(str(ctx.author.id), steamID)
    
    #formats correct responce back
    msg = ""
    if new_profile:
        msg = '```New infomation added```'
    else:
        msg = '```Your information has been updated```'

    #sends message back
    await ctx.send(msg)

# a background function to update the database
# updates hours played per game and adds new games purchased
# function only updates one member's library
@discord_client.command()
async def _update_lib(ctx, member):
    member = await get_user_class(member)
    usernames_list = db.get_all_members()
    # runs if memeber has steam info inputted
    if str(member.id) in usernames_list:
        steam_lib_link = db.get_steam_link(member)
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

        for game in undicted_game_info:
            #makes dictionary for game to easily access information
            game_info_dict = ast.literal_eval(game)
            if 'hours_forever' in game_info_dict:
                steam_game_link = 'https://store.steampowered.com/app/' + str(game_info_dict['appid'])
            
                #opens connection to client website and downloads information
                uClient = uReq(steam_game_link)

                #mloads html content into variable
                page_html = uClient.read()
                #closes connection to client website
                uClient.close()

                #parse the html document, making soup object
                page_soup = soup(page_html, "html.parser")

                json_script = page_soup.find_all("a", class_="app_tag")
                tags = []
                db_multiplayer = False
                for tag in json_script:
                    tag = tag.next.replace('\n', '').replace('\r', '').replace('\t', '')
                    tags.append(tag)
                    if tag == "Multiplayer":
                        db_multiplayer = True
                
                #updates Rpi database
                db.update_db(ctx.guild.name, member.name ,game_info_dict,', '.join(tags), db_multiplayer)
            #await ctx.send("```I do not have a Steam ID for you, please go input one with the 'steamid' command```")
            
        await ctx.send("```Your library has been updated```")
    else:
        await ctx.send("```Member does not exsist in my database. Use the steamID command to get started```")

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
async def uninstall(ctx, game_query=None):
    member = await get_user_class(ctx.author.mention)
    #calls search command with 'Download' perameter
    results, results_lib = await Search_func(ctx, game_query, None, called_from='Uninstall')
    
    @discord_client.event
    async def on_reaction_add(reaction, user):
        if user != discord_client.user:
            
            if reaction.emoji in results_lib.NavigationReacts:
                await reaction.message.delete()
                if reaction.emoji == results_lib.NavigationReacts[0]:
                    results_lib.PreviousPage()
                elif reaction.emoji == results_lib.NavigationReacts[1]:
                    results_lib.NextPage()

                response = await ctx.send(embed=results_lib.CurrentPage())
                await results_lib.React(response,'Uninstall')

            if reaction.emoji in results_lib.DownloadReacts:
                game_num = results_lib.PageNumber * results_lib.MaxGamesOnPage + results_lib.DownloadReacts.index(reaction.emoji)
                download_query = results_lib.data_array[game_num][2]
                name = results_lib.data_array[game_num][0]
                db.mark_as(ctx.guild, member.name, download_query, False)
                await ctx.send('```{0} has been marked as unistalled```'.format(name))
#discord_client.loop.create_task(update_libs())
discord_client.run(TOKEN)