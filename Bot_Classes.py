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
        Possible_formats = ['f','n','a','h','s','o','d']
        formatted_details = ''
        if 'n' in formatting:
            name_type = self.Nickname
        else:
            name_type = self.FullName

        if len(formatting) > 2:
            for char in formatting[1::]:
                if char in Possible_formats:
                    if char == 'a':
                        formatted_details += 'Hours: '+self.HoursPlayed+'\n'+'Steam store link: '+self.StorePage+'\n'+'Online: '+self.Multiplayer+'\n'+'Downloaded: '+self.Downloaded
                    else:
                        if char == 'h':
                            formatted_details += 'Hours: ' + self.HoursPlayed
                            formatted_details += '\n'
                        if char == 's':
                            formatted_details += 'Steam store link: ' + self.StorePage
                            formatted_details += '\n'
                        if char == 'o':
                            formatted_details += 'Online: ' + self.Multiplayer
                            formatted_details += '\n'
                        if char == 'd':
                            formatted_details += 'Downloaded: ' + self.Downloaded
                            formatted_details += '\n'
                    Possible_formats.remove(char)
        return name_type, formatted_details