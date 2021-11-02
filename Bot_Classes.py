import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.request import urlopen as uReq
import asyncio
import ast
from bs4 import BeautifulSoup as soup
from Bot_Classes import *

class Game:
    def __init__(self, Data : list):
        self.Owner = str(Data[0])
        self.FullName = str(Data[1])
        self.HoursPlayed = str(Data[2])
        self.SteamID = str(Data[3])
        self.StorePage = str(Data[4])
        self.Multiplayer = str(Data[5])
        self.Downloaded = str(Data[6])
        self.Nickname = str(Data[7])

    def Format_Details(self, formatting):
        Possible_formats = ['f','n','a','h','s','o','d','i']
        formatted_details = ''
        if 'n' in formatting:
            name_type = self.Nickname
        else:
            name_type = self.FullName

        for char in formatting[1::]:
            if char in Possible_formats:
                if char == 'a':
                    formatted_details += 'Hours: '+self.HoursPlayed+'\n'+'Steam store link: '+self.StorePage+'\n'+'Online: '+self.Multiplayer+'\n'+'Downloaded: '+self.Downloaded
                    break
                else:
                    if char == 'h':
                        formatted_details += 'Hours: ' + self.HoursPlayed
                    if char == 's':
                        formatted_details += 'Steam store link: ' + self.StorePage
                    if char == 'o':
                        formatted_details += 'Online: ' + self.Multiplayer
                    if char == 'd':
                        formatted_details += 'Downloaded: ' + self.Downloaded
                    if char == 'i':
                        formatted_details += 'Steam ID: ' + self.SteamID
                    if not char == formatting[-1]:
                        formatted_details += '\n'
                Possible_formats.remove(char)
        return name_type, formatted_details

class Library:
    def __init__(self, User=None, data=None):
        self.User = User.replace('!', '')
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

    def AddPage(self):
        #adds the current page to the embed list
        self.Embeds.append(self.Page)
        #Replace page with basic page again
        self.Page = self.NewEmbed()

    def NewEmbed(self):
        #Creates variable used to reset the page variable after adding it to the Library list
        if self.User == "Common Games":
            return discord.Embed(title = self.User, description = "Games played by all mentioned people" , color = discord.Color.blue())
        elif self.User == "results":
            return discord.Embed(title = "Search " + self.User, description = "Shows all games with search value in name" , color = discord.Color.green())
        else:
            return discord.Embed(title = self.User + "'s library", description = "Mentioned user's library" , color = discord.Color.orange())

    def NextPage(self):
        self.PageNumber += 1

    def PreviousPage(self):
        self.PageNumber -= 1
    
    def CurrentPage(self):
        return self.Embeds[self.PageNumber]

    async def React(self, response, download):
        if len(self.Embeds) > 1:
            if self.PageNumber == 0:
                await response.add_reaction(self.InitialReacts[1])
            elif self.PageNumber == len(self.Embeds)-1:
                await response.add_reaction(self.InitialReacts[0])
            else:
                for emoji in self.InitialReacts:
                    await response.add_reaction(emoji)

        if download == True:
            for emoji in self.DownloadReacts:
                await response.add_reaction(emoji)