import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.request import urlopen as uReq
import asyncio
import ast
from bs4 import BeautifulSoup as soup
from Bot_Classes import *
import os

#gets current directory for reading security files
cwd = os.getcwd()

#things to get setup with google, being authorized and whatnot
scope = [
    "https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

#credentials in list
print(cwd)
creds = ServiceAccountCredentials.from_json_keyfile_name(cwd +"\\creds.json", scope)

#passes in all credentials to make sure changes/ viewing are allowed
sheets_client = gspread.authorize(creds)

# Open the spreadhseet
wb = sheets_client.open('discord_bot_data')

#open
wks = wb.get_worksheet(0)

# class to hold individual game data
class Game:
    #declare callable variables
    def __init__(self, Data : list):
        self.Owner = str(Data[0])
        self.FullName = str(Data[1])
        self.HoursPlayed = str(Data[2])
        self.SteamID = str(Data[3])
        self.StorePage = str(Data[4])
        self.Multiplayer = str(Data[5])
        self.Downloaded = str(Data[6])
        self.Nickname = str(Data[7])

    # function to build details specified by the member 
    def Format_Details(self, formatting):
        #listing all possible formatting details
        Possible_formats = ['f','n','a','h','s','o','d','i']
        #creates a empty string to hold details as they are built
        formatted_details = ''

        #outdated format option 'nickname
        ########### needs removal###########
        if 'n' in formatting:
            name_type = self.Nickname
        else:
            name_type = self.FullName

        #checks all format details one at a time but the first
        for char in formatting[1::]:

            #check if the format option is a valid one
            if char in Possible_formats:

                #formats all details if 'a' is selected
                if char == 'a':
                    formatted_details += 'Hours: '+self.HoursPlayed+'\n'+'Steam store link: '+self.StorePage+'\n'+'Online: '+self.Multiplayer+'\n'+'Downloaded: '+self.Downloaded
                    break
                #other options format their respective details
                else:
                    #hour count playing the game
                    if char == 'h':
                        formatted_details += 'Hours: ' + self.HoursPlayed
                    #shows a link to the Steam's game page
                    if char == 's':
                        formatted_details += 'Steam store link: ' + self.StorePage
                    #shows if its multiplayer compatable
                    if char == 'o':
                        formatted_details += 'Online: ' + self.Multiplayer
                    #shows if the mentioned user currently has it downloaded
                    if char == 'd':
                        formatted_details += 'Downloaded: ' + self.Downloaded
                    #for trouble shooting only
                    #shows games unique ID
                    if char == 'i':
                        formatted_details += 'Steam ID: ' + self.SteamID
                    #adds new line character after each detail is formated for readability
                    if not char == formatting[-1]:
                        formatted_details += '\n'
                #removes the formatted option temporarily so that a double format doesn't occure
                Possible_formats.remove(char)
        #returns fully formatted string to add to embed
        return name_type, formatted_details

# class to hold multiple game info at once
class Library:
    # init class variable
    def __init__(self, User=None, data=None):
        self.User = User
        self.PageNumber = 0
        if data == None:
            self.data_array = []
        else:
            self.data_array = data
        self.Embeds = []
        self.MaxGamesOnPage = 5
        #creates variable to check how many games the program has done to know when to stop looking
        self.GameCount = len(self.Embeds)
        #creates a copy of the basic page
        self.Page = self.NewEmbed()
        self.InitialReacts = ['⏪', '⏩']
        self.DownloadReacts = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣']

    # add an embed page
    def AddPage(self):
        #adds the current page to the embed list
        self.Embeds.append(self.Page)
        #Replace creation page with basic page again
        self.Page = self.NewEmbed()

    # function for creating new embed page
    # displays different kinds of information
    def NewEmbed(self):
        #checks if embed is for comparing libraries
        if self.User == "Common Games":
            return discord.Embed(title = self.User, description = "Games played by all mentioned people" , color = discord.Color.blue())
        #checks if embed is a search result
        elif self.User == "results":
            return discord.Embed(title = "Search " + self.User, description = "Shows all games with search value in name" , color = discord.Color.green())
        #standard call for an individual member
        else:
            return discord.Embed(title = self.User + "'s library", description = "Mentioned user's library" , color = discord.Color.orange())

    # increments what page is shown in discord
    def NextPage(self):
        self.PageNumber += 1

    # decrements what page is shown in discord
    def PreviousPage(self):
        self.PageNumber -= 1
    
    # returns current embed page 
    def CurrentPage(self):
        return self.Embeds[self.PageNumber]

    # defines what reactions do what when a member uses them
    async def React(self, response, download):
        #checks if there is embeds to show
        if len(self.Embeds) > 1:
            # if its the first page only add the forward reaction
            if self.PageNumber == 0:
                # reacts with emoji
                await response.add_reaction(self.InitialReacts[1])
            # if its the last page only add the backward reaction
            elif self.PageNumber == len(self.Embeds)-1:
                # reacts with emoji
                await response.add_reaction(self.InitialReacts[0])
            # if its any page besides first or last then add all reactions
            else:
                #loops through all reactions
                for emoji in self.InitialReacts:
                    # reacts with emoji
                    await response.add_reaction(emoji)
        # if the member wants to mark games as downloaded in the data base
        if download == True:
            # loop though each download reaction
            # 1 - 5 emojis "downloads" the respective game shown in the list
            for emoji in self.DownloadReacts:
                # reacts with emoji
                await response.add_reaction(emoji)
