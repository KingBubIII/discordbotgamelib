import discord
from discord.ext import commands
from discord.ui import Button, View
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.request import urlopen as uReq
import asyncio
import ast
from bs4 import BeautifulSoup as soup
from Bot_Classes import *
import platform 

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
        Possible_formats = ['h','s','o','d','i']
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
    
    async def getView(self):

        # creates an element for a response with discord buttons 
        myView = View()
        
        if self.PageNumber > 0:
            if self.PageNumber > 1:
                myView.add_item(self.beginning)
            myView.add_item(self.backward)

        if self.PageNumber < len(self.Embeds)-1:
            myView.add_item(self.forward)
            if self.PageNumber < len(self.Embeds)-1:
                myView.add_item(self.end)

        return myView

    # returns current embed page 
    def CurrentPage(self):
        return self.Embeds[self.PageNumber]

    async def BEGINNING(self, interaction):
        self.PageNumber = 0
        await interaction.response.edit_message(embed=self.CurrentPage(), view=await self.getView())

    async def FORWORD(self, interaction):
        if self.PageNumber < len(self.Embeds)-1:
            self.PageNumber += 1
        else:
            self.PageNumber = 0
        await interaction.response.edit_message(embed=self.CurrentPage(), view=await self.getView())

    async def BACKWORD(self, interaction):
        if self.PageNumber > 0:
            self.PageNumber -= 1
        else:
            self.PageNumber = len(self.Embeds)-1
        await interaction.response.edit_message(embed=self.CurrentPage(), view=await self.getView())

    async def END(self, interaction):
        self.PageNumber = len(self.Embeds)-1
        await interaction.response.edit_message(embed=self.CurrentPage(), view=await self.getView())
    
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
        self.NavigationReacts = ['⏪', '◀️', '▶️', '⏩']
        self.DownloadReacts = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣']
        self.Possible_formats = ['h','o','d','t']
        
        self.beginning = Button( style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[0], row=0)
        self.beginning.callback = self.BEGINNING
        
        self.forward = Button(style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[2], row=0)
        self.forward.callback = self.FORWORD
        
        self.backward = Button(style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[1], row=0)
        self.backward.callback = self.BACKWORD
        
        self.end = Button(style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[3], row=0)
        self.end.callback = self.END