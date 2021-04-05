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

def update_lib(member_name):
    
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
        print(len(undicted_game_info))
        #sets game info sheet to active
        wks = wb.get_worksheet(0)
        
        #gets the current sheet to be compared to tell if new games needed to be added
        current_sheet = wks.get_all_values()

        myfile = open("test.txt",'w')

        for game in undicted_game_info:
            tags = []
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

                result = ''
                for element in useful_game_info: 
                    result += str(element) + ", "
                result += "\n"
                myfile.write(result)
                #print(useful_game_info)
        myfile.close()

update_lib("<@!212019850510467072>")
#update_lib("<@!237078783650168833>")