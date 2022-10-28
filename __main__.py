#!/usr/bin/python3
import discord
from discord.ext import commands
from discord.ui import Button, View
from urllib.request import urlopen as uReq
import ast
from bs4 import BeautifulSoup as soup
from matplotlib.backend_bases import cursors
from Bot_Classes import *
import platform
import random as rd
import Rpi_db as db
import itertools
import time
import DB_BG_update

# gets token from local file
# uses linux or windows paths as needed
TOKEN = open(('/home/kingbubiii/Documents/discordbotgamelib/' if platform.system() == 'Linux' else '') + 'token.txt').read()
# print(TOKEN)

# creating client instance and identifying prefix for commands 
intents = discord.Intents.default()
intents.members = True

discord_client = commands.Bot(intents=intents)
discord_client.remove_command('help')

# allows users to search libraries, their own or others, for game names
async def Search_func(ctx, search_query, member, called_from):
    results_data = db.search(member.name, search_query, called_from)
    #print(results_data)
    if len(results_data) == 0:
        await ctx.respond('```I found no matches```')
        return False
    #creates a new library from results list 
    results_lib = Library(User="results", data=results_data, called_from=called_from)
    #creates embed from result class
    await create_embeds(results_lib, None)
    #send result embed
    return results_lib

# formats serveral pages of embeds using the format details specified by user
async def create_embeds(libclass, members):
    # loops through each common game
    for count, game in enumerate(libclass.data_array):
        # if only one library is being read 
        if type(libclass.data_array[0][1]) == str:
            # adds a field per game to the embed with the formatting options
            libclass.Page.add_field(name=game[0], value=game[1], inline=False)
        
        # if details of multiple users are being outputed
        elif type(libclass.data_array[0][1]) == list:
            # empty string to be added to as needed
            formatted = ""
            #the number of details specified
            details_len = len(game[1][0].split('\n'))
            
            # loops through all members 2 at a time
            for index in range(0,len(members), 2):
                # allows for an odd person that will no be grouped with someone else 
                grouped_people = 1 if index+1 == len(members) else 2

                """
                '\u200b' is a zero width space character
                It is used because discord embeds like to remove excess spaces and new lines
                This trickes the embed so it doesn't remove extra spaces and new lines
                Therefore allows for formatting
                """

                # loops though the grouped members
                for shift in range(grouped_people):
                    # will bold member name 
                    temp_str = '**' + members[index+shift] + '**'
                    # centers the name in zero width characters
                    temp_str = temp_str.center(32+4, '\u200b')
                    #replaces the zero width characters with spaces followed by the special character
                    temp_str = temp_str.replace('\u200b',' \u200b')
                    # adds string to final result
                    formatted += temp_str
                
                # sperates the member names from the details with a newline
                formatted += '\n\u200b'

                # loops through each game detail
                for i in range(details_len):
                    # does this for each grouped member
                    for shift in range(grouped_people):
                        # grabs the detail 
                        temp_str = game[1][index+shift].split('\n')[i]
                        # centers the game detail to line up with the member name
                        temp_str = temp_str.center(32+4, '\u200b')
                        # adds the space with the special character
                        temp_str = temp_str.replace('\u200b',' \u200b')
                        # adds string to final result
                        formatted += temp_str
                        # adds new line only inbetween details and the next grouped member names
                        if shift+1 == grouped_people and (index+1 != len(members) or i+1 != details_len):
                            formatted += '\n\u200b'

            #print(len(formatted))
            libclass.Page.add_field(name=game[0], value=formatted, inline=False)
        
        # checks to make sure there is only 5 games per page of the library so it doesnt get overwhelming and the embed cant hold the whole library
        if (((count+1)%libclass.MaxGamesOnPage) == 0 and count > 0) or count - len(libclass.data_array) == 0:
            libclass.AddPage()
    #if there are 5 or less items
    if  len(libclass.Page.fields) != 0:
        libclass.NumOfNumReacts = len(libclass.Page.fields)
        libclass.AddPage()

# allows command function arguments to be called from anywhere when using a command
async def Arg_Assign(all_args):

    # filters down entire list of arguments down to ones with member character tags '<@!'
    # converts from tuple to list
    members = list(filter(lambda arg: "<@" in arg , all_args))
    
    # checks if there is a format choice or not
    # if no
    if len(members) == len(all_args):
        #format becomes none type
        misc = None
    # if yes
    else:
        #make format a list of all the arguments
        misc = list(all_args)

        # remove all member arguemnts so misc is left alone
        for member in members:
            misc.remove(member)
        #format becomes string from list
        misc = misc[0]
    
    # if only one member is mentioned, convert it to a string instead of leaving it in an array
    if len(members) == 1:
        members = members[0]
    elif len(members) == 0:
        members = None

    return members, misc

# a function to show similarities between members' libraries
# can compare two or more members at a time
async def compare_func(ctx, formatting, members):

    Common_lib = Library(User = "Common Games")
    db.compare(members, Common_lib, formatting)
    await create_embeds(Common_lib, members)
    return Common_lib

async def get_user_class(member_id_str):
    member_class = discord_client.get_user(int(member_id_str.replace('<@','').replace('>','').replace('!','')))
    return member_class

# signal that the bot is online and ready to be used
# Set the help command to be what the bot is "playing"
@discord_client.event
async def on_ready():
    print('Ready set let\'s go')
    await discord_client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="/help"))

@discord_client.slash_command(name = "compare", description = "Look at common games between multiple people libraries")
async def compare(  ctx: discord.ApplicationContext,
                    members: discord.Option( str, description="mention multiple people in here", required=True),
                    formatting: discord.Option( str, description="formatting options exactly like readlib command", required=False)):

    real_members = []
    for item in members.split(" "):
        if "<@" in item:
            temp_user = await get_user_class(item)
            real_members.append(temp_user.name)

    Common_lib = await compare_func(ctx, formatting, real_members)

    response = await ctx.respond(embed=Common_lib.CurrentPage(), view= await Common_lib.getView())

# member command to update database games as downloaded
@discord_client.slash_command(name = "download", description = "Allows you to write to the database to display what game you can play")
async def download( ctx: discord.ApplicationContext, 
                    search_query: discord.Option( str, description="Use this just like the search command", required=False) = None):
    #calls search command with 'Download' perameter
    results_lib = await Search_func(ctx, search_query, ctx.author, called_from='download')

    await ctx.respond(embed=results_lib.CurrentPage(), view = await results_lib.getView(), ephemeral=True)

# A simple command that repeats what was sent
# mainly useful for debugging 
# @discord_client.command() 
@discord_client.slash_command(name = "echo", description = "Say hello to the bot")
async def echo(ctx, msg: str = 'echo'):
    # await ctx.respond(f"""```{ctx.author.id}: {msg}```""")
    # await ctx.respond(f"""```{ctx.guild}```""")
    await ctx.respond(f"""```{msg}```""")
    # test = discord.Embed(title = 'test', description = '\u00ae'*5 , color = discord.Color.blue())
    # await ctx.respond(embed=test)

# teaches members how to use bot
# you can specify commands to get in-depth help on them
@discord_client.slash_command(name = "help", description = "shows the list of avaible commands with a few examples")
async def help( ctx: discord.ApplicationContext, 
                command: discord.Option(str, 'Specify a command name to get more in depth help', required=False) = None):
    
    helpEmbed = discord.Embed(title = 'basic bitch', color = discord.Color.orange())

    if command == None:
        helpEmbed.title = 'List of short command descriptions'
        helpEmbed.add_field(name = 'compare', value = 'Shows common games between all mentioned people in pagified version like reading a library', inline=False)
        helpEmbed.add_field(name = 'download', value = 'Page through library to select what games are downloaded locally on your pc', inline=False)
        helpEmbed.add_field(name = 'echo', value = 'Repeats what you say in a fancy code block', inline=False)
        helpEmbed.add_field(name = 'readlib', value = 'Shows what games you have in your Steam library and details associated with it', inline=False)
        helpEmbed.add_field(name = 'search', value = 'Returns list of games in anyone\'s library that matches your search term', inline=False)
        helpEmbed.add_field(name = 'steamid', value = 'Either creates new profile for you in my database or updates your exsisting profile', inline=False)
        # helpEmbed.add_field(name = 'download', value = '', inline=False)


    elif command == 'echo':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = command, value = 'Repeats what you say in a fancy code block\n\n\
                                                        Optional command(s): message\n\n\
                                                        Default message to \'echo\'\n\n\
                                                        The arguement can be as long as you want including spaces\n\n \
                                                        Default Example: >>echo\nDefault Ouptut: echo\n\n\
                                                        Filled argument Example: >>echo This command is useless \n\
                                                        Filled arguement Output: This command is useless')
        helpEmbed.add_field(name = 'Examples', value = '>>echo testing testing')

    elif command == 'readlib':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = command, value = 'Mention a person to read their library\n\n\
                                                        Manditory command(s): username\nOptional command(s): formatting\n\n\
                                                        Specify formatting by a \'-\' then put any combination of the letters\
                                                        \'a\' \'h\' \'o\' \'d\' \'t\'\n\n\
                                                        \'a\' (All): It will display all avaiable info options\n\
                                                        \'h\' (Hours): Displays the number of hours you\'ve put into the game\n\
                                                        \'o\' (Online): Displays if the game is multiplayer\n\
                                                        \'d\' (Downloaded): Displays if you have the game downloaded\n\
                                                        \'t\' (Tags): Shows all the tags Steam has associated with it')
        

        helpEmbed.add_field(name = 'Examples', value = '>>readlib @KingBubIII\n\n\
                                                        >>readlib @KingBubIII -a\n\n\
                                                        >>readlib @KingBubIII -hd\n\n\
                                                        >>readlib @KingBubIII -dhos\n\n')

    elif command == 'compare':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = command, value = 'See all games each mentioned person has in common\n\
                                                        Can also show details using the details option of readlib')
        helpEmbed.add_field(name = 'Examples', value = '>>compare @KingBubIII @Test123\n\n\
                                                        >>compare @KingBubIII   @Test123 -d\n\
                                                        Shows common games that are downloaded\n\n\
                                                        >>compare @KingBubIII @Test123 -hso\n\
                                                        Shows common games while showing hours, Steam link, and if its multiplayer for each player')

    elif command == 'download':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = command, value = 'This function allows you to mark games as downloaded in my database\n\n\
                                                        The output is the same as a readlib command but with numbered reaction options\n\n\
                                                        Reacting with a numbered reaction will mark that game on the current page as downloaded\n\n\
                                                        You are the only one that can mark games as downloaded in your library\n\n')
        helpEmbed.add_field(name = 'Examples', value = '>>download')

    elif command == 'steamid':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = command, value = 'Update your steam ID in my database\n\n\
                                                            If you\'re new, I\'ll create a new profile in my database and add your ID.\n\n\
                                                            Your steam ID directs me to your Steam profile.\n\n\
                                                            Make sure you set your acount to public though!')
        helpEmbed.add_field(name = 'Examples', value = '>>steamid 76561198286078396\n\n\
                                                        >>steamid 12345678912345678')

    elif command == 'search':
        helpEmbed.title = 'In depth help for'
        helpEmbed.add_field(name = command, value = 'Just a basic search function\n\n\
                                                        The default library to search if you don\'t mention a person is your own\n\n\
                                                        Be as specific or as general as you would like\n\n\
                                                        Can only search one person\'s library at a time\n\n')
        helpEmbed.add_field(name = 'Examples', value = '>>search ba @KingBubIII\n\n\
                                                        >>search ba')

    # elif command == '':
        # helpEmbed.title = 'In depth help for'
        # helpEmbed.add_field(name = command, value = 'explain')
        # helpEmbed.add_field(name = 'Examples', value = 'stuff')

    await ctx.respond(embed=helpEmbed)

# sends a discord embed that users can page through to view all games and details in database
# anyone can call to read another persons library
# @discord_client.command()
@discord_client.slash_command(name = "readlib", description = "Read a specific person's library by mentioning them")
async def readlib(  ctx: discord.ApplicationContext, 
                    member: discord.Option(discord.Member, 'Mention only one person', required=True),
                    details: discord.Option(str, 'You can use any number and combination of ', required=False)):

    # creates library for user
    UsersLibrary = Library(User=member.name)

    # fetches library info from mysql database
    db.readlib(UsersLibrary, details)
    # creates embed pages
    await create_embeds(UsersLibrary, None)
    
    # sends inital reponse
    await ctx.respond(embed=UsersLibrary.CurrentPage(), view=await UsersLibrary.getView(), ephemeral=True if ctx.author.name == member.name else False)

# runs the Search_func command
#@discord_client.command()
@discord_client.slash_command(name = "search", description = "Search's a mentioned users library with your query")
async def search(   ctx: discord.ApplicationContext,
                    member: discord.Option(discord.Member, 'Mention only one person', required=True),
                    query: discord.Option(str, 'search a term or the starting letter', required=True) ):

    #runs search command without being intention to change database values 
    response_lib = await Search_func(ctx, query, member, 'search')
    
    await ctx.respond(embed=response_lib.CurrentPage(), view=await response_lib.getView())

@discord_client.slash_command(name = "steamid", description = "This is basically your profile in my database")
async def steamid(  ctx: discord.ApplicationContext, 
                    steamid: discord.Option(str, 'Find your Steam ID in your \'Account Details\'', required=True) ):

    channels = [channel[1] for channel in db.channel_info()]

    if not ctx.guild.name in channels:
        db.add_channel(ctx.guild.name)

    #updates mysql database and returns boolean value
    new_profile = db.profile_update(str(ctx.author.id), steamid, ctx.author.name)
    
    #formats correct responce back
    msg = "Please wait for a few minutes for you library to update.```"
    if new_profile:
        msg = '```New infomation added. ' + msg
    else:
        msg = '```Your information has been updated. ' + msg

    #sends message back
    await ctx.respond(msg, ephemeral=True)

    DB_BG_update.update_lib(ctx.author.name)

# a background function to update the database
# updates hours played per game and adds new games purchased
# function only updates one member's library
@discord_client.slash_command(name = "update_lib", description = "Only my creator can use this command. This will eventually be a background task")
async def _update_lib(  ctx: discord.ApplicationContext,
                        member: discord.Option(discord.User, 'Mention user who library needs updating', required=True) ):
    
    DB_BG_update.update_lib(member.name)

# will give a common game suggestion between all mentioned members
@discord_client.slash_command(name = "random", description = "Get a random game that all mentioned users own.")
async def random(   ctx: discord.ApplicationContext, 
                    members: discord.Option( str, description="Mention multiple people in here", required=True),
                    downloaded: discord.Option(str, 'Searches only games that are downloaded for all parties', required=False, choices=["Yes", "No"], default = "Yes")):
    
    members = members.split(" ")
    members = [ await get_user_class(member) for member in members if "<@" in member]
    members = [ member.name for member in members]
    
    # get a result class
    results = db.get_master_and_member_game_data(members, True)
    results = [game_name[1] for game_name in results]
    
    # select random element in the list, therefore random game
    random_game = rd.choice(results)
    # send chosen game embed
    await ctx.respond("```{0}```".format(random_game))

@discord_client.slash_command(name = "uninstall", description = "Allows you to write to the database to remove what games are displayed that you can play")
async def uninstall(    ctx: discord.ApplicationContext, 
                        search_query: discord.Option( str, description="Use this just like the search command", required=False) = None):
    
    results_lib = await Search_func(ctx, search_query, ctx.author, called_from='uninstall')
    await ctx.respond(embed=results_lib.CurrentPage(), view = await results_lib.getView(), ephemeral=True)
discord_client.run(TOKEN)