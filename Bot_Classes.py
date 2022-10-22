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
import Rpi_db as db

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

        if self.called_from == 'download' or self.called_from == 'uninstall':
            maxindex = 5 if self.PageNumber != len(self.Embeds)-1 else self.NumOfNumReacts
            for index in range(maxindex):
                myButton = Button( style=discord.ButtonStyle.grey, emoji=self.NumReacts[index], row=1)
                myButton.callback = self.MARK_AS
                myView.add_item(myButton)

        self.view = myView
        return self.view

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

    async def MARK_AS(self, interaction):
        button = discord.utils.get(self.view.children, custom_id=interaction.custom_id)
        
        gameid = self.data_array[(self.PageNumber*self.MaxGamesOnPage) + self.NumReacts.index(button.emoji.name)][2]
        if self.called_from == 'download':
            set_as = True
        elif self.called_from == 'uninstall':
            set_as = False
        else:
            set_as = None
        
        marked = db.mark_as(interaction.user.name, gameid, set_as)

        await interaction.channel.send("{0} has been marked as {1}".format(marked[0], 'downloaded' if marked[1] == 1 else 'uninstalled'))
    
    # init class variable
    def __init__(self, User=None, data=None, called_from=None):
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
        self.NumReacts = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣']
        self.Possible_formats = ['h','o','d','t']
        self.called_from = called_from
        self.view = View()
        self.NumOfNumReacts = 5
        
        self.beginning = Button( style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[0], row=0)
        self.beginning.callback = self.BEGINNING
        
        self.forward = Button(style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[2], row=0)
        self.forward.callback = self.FORWORD
        
        self.backward = Button(style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[1], row=0)
        self.backward.callback = self.BACKWORD
        
        self.end = Button(style=discord.ButtonStyle.grey, emoji=self.NavigationReacts[3], row=0)
        self.end.callback = self.END