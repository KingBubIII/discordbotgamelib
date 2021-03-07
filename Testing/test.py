import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.request import urlopen as uReq
import asyncio
import ast
from bs4 import BeautifulSoup as soup
from Bot_Classes import *

scope = [
    "https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

#credentials in list
creds = ServiceAccountCredentials.from_json_keyfile_name("reputation_creds.json", scope)

#passes in all credentials to make sure changes/ viewing are allowed
sheets_client = gspread.authorize(creds)

InitialReacts = ['\u23EA', '\u23E9']

wb = sheets_client.open('TBD test')

def update_lib(member_name):
    
    member_name = str(member_name).replace("!","")
    print(member_name)
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
                useful_game_info = [member_name, game_info_dict['name'], game_info_dict['hours_forever'], game_info_dict['appid'], 'https://store.steampowered.com/app/'+str(game_info_dict['appid']), 'TBD', 'no', 'none',]

            with open('test.txt','w') as myfile:
                myfile.write('\n')
                myfile.write(game)
                myfile.close()
            #find out if game is multiplayer and or other tags
            #add tags to spreadsheet
            #loops through each row in the games sheet to update and add new games to sheet
            
            row_count = 1
            
            for row in current_sheet:
                if row[:3] == useful_game_info[:3]:
                    wks.update_cell(row_count, 3, useful_game_info[2])
                row_count+=1
            if not useful_game_info[:3] in current_sheet:
                wks.append_row(useful_game_info,'RAW')
        #await ctx.send("```Your library has been updated```")


def readLib(user_mention, formatting=None):
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
        #response = await ctx.send(embed=library_embeds[0]) #len(library_embeds)-1])
    
    elif formatting[0] == '-':
        validQuery = True
        
        for char in formatting[1::]:
            if not char in ['f','n','a','h','s','o','d']:
                #await ctx.send(f"""```Format type unknown+{repr(char)}```""")
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
            #response = await ctx.send(embed=library_embeds[PageCount])
    
    for emoji in InitialReacts:
        pass
        #await response.add_reaction(emoji)

readLib("<@!237078783650168833>", "-h")
#update_lib("<@!237078783650168833>")