import urllib.request
from csv import DictReader
import io
import os

file_found = False
for filename in os.listdir('.'):
    if filename.startswith("main_registration_data"):
        main_reg_filename = filename
        file_found = True
        break
if not file_found:
    raise Exception("Main registration data file not found")

print(main_reg_filename)


# with urllib.request.urlopen('https://aga-functions.azurewebsites.net/api/GenerateTDListA') as response:
#    html = response.read().decode('utf-8')
#    tdList = DictReader(io.StringIO(html), delimiter='\t', fieldnames=['Name', 'AGAID', 'Member Type', 'Rating', 'Expiration Date', 'Chapter Code', 'State', 'Sigma', 'Join Date'])
   
