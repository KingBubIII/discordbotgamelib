import gspread
from oauth2client.service_account import ServiceAccountCredentials
"""
scope = [
    "https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

#credentials in list
creds = ServiceAccountCredentials.from_json_keyfile_name("reputation_creds.json", scope)

#passes in all credentials to make sure changes/ viewing are allowed
sheets_client = gspread.authorize(creds)
"""

import random
unordered = list(range(10))
ordered = []
i = 0

random.shuffle(unordered)

print(unordered)
lowest = unordered[0]

while len(unordered) > 0:
    print(unordered[i])
    if  unordered[i] < lowest:
        lowest = unordered[i]
    i += 1
    print(len(unordered))
    if i == len(unordered):
        ordered.append(lowest)
        unordered.remove(lowest)
        if unordered:
          lowest = unordered[0]
        i = 0

print(ordered)