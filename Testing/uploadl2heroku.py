import os
import sys

#single file upload
def one_file(file_name):
    os.system('git add .')
    os.system('git commit -m ' + file_name)
    os.system('git push heroku master')

def multiple_files(note):
    os.system('git add .')
    os.system('git commit -am ' + note)
    os.system('git push heroku master')

header = print('To upload mulitple files enter "-am" followed by your version change in quotes\nTo upload one file put -m followed by the file name with the extention')
user_input = input()

amt_of_files, file_name_or_note = user_input.split(' ')

if amt_of_files == '-m':
    one_file(file_name_or_note)
elif amt_of_files == '-am':
    multiple_files(file_name_or_note)
else:
    print('you entered it wrong')