import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.request import urlopen as uReq
import asyncio
import ast
from bs4 import BeautifulSoup as soup
from Bot_Classes import *

#things to get setup with google, being authorized and whatnot
scope = [
    "https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

#credentials in list
creds = ServiceAccountCredentials.from_json_keyfile_name("reputation_creds.json", scope)

#passes in all credentials to make sure changes/ viewing are allowed
sheets_client = gspread.authorize(creds)

# Open the spreadhseet
wb = sheets_client.open('discord_bot_data')

#discord bot token needed to run bot
TOKEN = 'NTY3ODYxODM2MTAwMjcyMTI4.XLZ4Dw.tP4m4pQXGUy9EBDssa2JwLyiM2Y'

#creating client instance and identifying prefix for commands 
prefix = '>>'
discord_client = commands.Bot(command_prefix=prefix)
#discord_client.case_insensitive = True
#removing default help command
discord_client.remove_command('help')

InitialReacts = ['\u23EA', '\u23E9']

PageCount = 0

#Setting the help command to be what the bot is playing 
@discord_client.event
async def on_ready():
    print('Ready set let\'s go')
    await discord_client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=prefix + "help"))

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
                useful_game_info = [member_name, game_info_dict['name'], game_info_dict['hours_forever'], game_info_dict['appid'], 'https://store.steampowered.com/app/'+str(game_info_dict['appid']), 'No', 'no', 'none',]

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
            await ctx.send("```Your library has been updated```")
        else:
            await ctx.send("```I do not have a Steam ID for you, please go input one with the 'steamID' command```")

@discord_client.command()
async def download(ctx, GameIndex):
    pass

@discord_client.command()
async def steamID(ctx, input_id):
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
async def help(ctx, commandName=None):

    if commandName == None:
        helpEmbed = discord.Embed(title = 'List of short command descriptions', color = discord.Color.orange())
        helpEmbed.add_field(name = 'Command Prefix: ', value =  'put this, "' + prefix + '", in front of specified command name to be able to call the command', inline=False)
        helpEmbed.add_field(name = 'help', value = 'One optional arguement: commandName\nSpecify a command\'s name to get more details on that command', inline=False)
        helpEmbed.add_field(name = 'echo', value = 'Repeats what you say in a fancy code block', inline=False)
        helpEmbed.add_field(name = 'readLib', value = 'Allows you and others to read the games you have installed.', inline=False)
        helpEmbed.add_field(name = 'delItem', value = 'Deletes specified item from library', inline=False)
        helpEmbed.add_field(name = 'steamID', value = 'Either creates new profile for member or updates exsisting Steam ID number', inline=False)


    elif commandName == 'echo':
        helpEmbed = discord.Embed(title = 'In depth help for ', color = discord.Color.orange())
        helpEmbed.add_field(name = commandName, value = 'Repeats what you say in a fancy code block\n\nOne optional arguement: message\n\nIf the arguement is not filled then the message defaults to \'echo\'\n\nThe arguement can be as long as you want including spaces\n\n Default Example: >>echo\nDefault Ouptut: echo\n\nFilled Argument Example: >>echo This command is useless \nFilled arguement Output: This command is useless')

    elif commandName == 'addItem':
        helpEmbed = discord.Embed(title = 'In depth help for ', color = discord.Color.orange())
        helpEmbed.add_field(name = commandName, value = 'Adds a game to your library for you and others to look at\n\nFour needed arguements: Game\'s name, Game\'s nickname, Launcher, and whether you can play with friends or not(yes or no)\n\nUse dashes where you want spaces in names, these will turn into spaces in your libray. However use spaces for distinguishing arguements\n\nExample: >>addItem The-Elder-Scrolls-V:-Skyrim Skyrim Steam Yes \nOuptut: Successfully added')

    elif commandName == 'readLib':
        helpEmbed = discord.Embed(title = 'In depth help for ', color = discord.Color.orange())
        helpEmbed.add_field(name = commandName, value = 'Allows you and others to read the games you have installed.\n\nThis command has one manditory command: username and one optional command: formatting\nSpecify your username or another person\'s in the server to read the users library of games\nThe formatting command allows your to read more or less details of the library of the user you specify. To do this you must put a \'-\' then put any number of and combination of the letters  \'f\' \'n\' \'a\' \'h\' \'s\' \'o\' \'d\'.\n\'f\': will make the full game\'s name part of the bot\'s output of the library.\n\'n\': will make the game\'s nickname part of the bot\'s output of the library.\n')

    await ctx.send(embed=helpEmbed)

@discord_client.command() 
async def echo(ctx, *, msg='echo'):
    await ctx.send(f"""```{msg}```""")
    
@discord_client.command()
async def readLib(ctx, user_mention, formatting=None):
    response = None
    #creates empty list to hold all the embeds created to be accessed by the user in discord
    library_embeds = []
    #open first sheet
    wks = wb.get_worksheet(0)
    #gets the whole game data worksheet as a single variable to be accessable with one read 
    current_sheet = wks.get_all_values()
    #gets the number of games the user has for the program to know when to stop looking for more games
    num_of_games = len(wks.findall(user_mention))
    #makes the specified user's id useable in the code
    user_mention = user_mention.replace('!', '')
    #creates an empty embed to be added to later as the infromation is parsed
    LibraryEmbed = discord.Embed(title = user_mention + "'s library", description = "Maximum of 5 games per page." , color = discord.Color.orange())
    #creates variable to check how many games the program has done to know when to stop looking
    embeded_game_count = 0
    
    #defaults to just the downloaded format option 
    if formatting == None:
        #looks at each row of the whole sheet individually
        for row in current_sheet:
            #skips the very first row of the sheet to skip the row headers
            if not row == current_sheet[0]:
                #creates an instance of the game class to make information more readable and accessable
                item = Game(row)
                #makes sure the owner of the current game instace is the user that was specified in the command
                if item.Owner == user_mention:
                    #increments the amount of games the specified person has to be shown
                    embeded_game_count += 1
                    #adds a field per game to the embed with the downloaded status
                    LibraryEmbed.add_field(name=item.FullName, value='Downloaded: ' + item.Downloaded, inline=False)
                    # checks to make sure there is only 5 games per page of the library so it doesnt get overwhelming and the embed cant hold the whole library
                    if embeded_game_count%5 == 0 or num_of_games - embeded_game_count == 0:
                        #adds the current embed to the embed list
                        library_embeds.append(LibraryEmbed)
                        #creates new blank embed so it can be added to again
                        LibraryEmbed = discord.Embed(title = user_mention + "'s library", description = "Maximum of 5 games per page." , color = discord.Color.orange())
        response = await ctx.send(embed=library_embeds[0]) #len(library_embeds)-1])
    
    elif formatting[0] == '-':
        validQuery = True
        
        for char in formatting[1::]:
            if not char in ['f','n','a','h','s','o','d']:
                await ctx.send(f"""```Format type unknown {repr(char)}```""")
                validQuery = False

        if validQuery == True:
            for row in current_sheet:
                if not row == current_sheet[0]:
                    item = Game(row)
                    if item.Owner == user_mention:
                        game_details = item.Format_Details(formatting)
                        embeded_game_count += 1
                        LibraryEmbed.add_field(name=game_details[0], value=game_details[1], inline=False)
                        if embeded_game_count%5 == 0 or num_of_games - embeded_game_count == 0:
                            library_embeds.append(LibraryEmbed)
                            LibraryEmbed = discord.Embed(title = user_mention + "'s library", description = "Maximum of 5 games per page." , color = discord.Color.orange())
            response = await ctx.send(embed=library_embeds[PageCount])
    
        for emoji in InitialReacts:
            await response.add_reaction(emoji)

    @discord_client.event
    async def on_reaction_add(reaction, user):
        if user != discord_client.user:
            global PageCount
            
            if reaction.emoji == InitialReacts[1]:
                await reaction.message.delete()
                if not PageCount+1 > len(library_embeds):
                    PageCount += 1

            if reaction.emoji == InitialReacts[0]:
                await reaction.message.delete()
                if not PageCount-1 < 0:
                    PageCount -= 1

            response = await ctx.send(embed=library_embeds[PageCount])

            for emoji in InitialReacts:
                await response.add_reaction(emoji)


    
#discord_client.loop.create_task(update_libs())
discord_client.run(TOKEN)