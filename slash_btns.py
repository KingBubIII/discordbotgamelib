import discord
from discord.ui import Button, View

class Navigation():
    async def BEGINNING(self, interaction):
        self.libClass.PageNumber = 0
        await interaction.response.edit_message(embed=self.libClass.CurrentPage())

    async def FORWORD(self, interaction):
        self.libClass.NextPage()
        await interaction.response.edit_message(embed=self.libClass.CurrentPage())

    async def BACKWORD(self, interaction):
        self.libClass.PreviousPage()
        await interaction.response.edit_message(embed=self.libClass.CurrentPage())

    async def END(self, interaction):
        self.libClass.PageNumber = len(self.libClass.Embeds)-1
        await interaction.response.edit_message(embed=self.libClass.CurrentPage())
    
    def __init__(self, libClass):
        self.libClass = libClass
        self.beginning = Button( style=discord.ButtonStyle.grey, emoji=self.libClass.NavigationReacts[0])
        self.beginning.callback = self.BEGINNING

        self.forward = Button(style=discord.ButtonStyle.grey, emoji=self.libClass.NavigationReacts[2])
        self.forward.callback = self.FORWORD

        self.backward = Button(style=discord.ButtonStyle.grey, emoji=self.libClass.NavigationReacts[1])
        self.backward.callback = self.BACKWORD

        self.end = Button(style=discord.ButtonStyle.grey, emoji=self.libClass.NavigationReacts[3])
        self.end.callback = self.END
