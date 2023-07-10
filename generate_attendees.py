import urllib.request
from csv import DictReader, writer, reader, DictWriter
import io
import os

attendees_filename = "attendees.csv"

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def get_unique_string(p):
    res = p['given_name'].lower()
    res += p['family_name'].lower()
    res += p['aga_id']
    return res

def get_rank_long(rank):
    res = rank[:-1]
    if rank[-1] == 'k':
        res += ' kyu'
    elif rank[-1] == 'd':
        res += ' dan'
    elif rank[-1] == 'p':
        res += ' pro'
    return res

# Search for main_registrant_data file
registrant_filename = adhoc_filename = final_ranks_filename = ''
for filename in os.listdir('.'):
    if filename.startswith("registrant_data"):
        registrant_filename = filename
    elif filename.startswith("congress_registrant_list"):
        adhoc_filename = filename
    elif filename.endswith("registrations.csv"):
        final_ranks_filename = filename

if not registrant_filename or not adhoc_filename or not final_ranks_filename:
    raise Exception("Missing registrant_data file or congress_registrant_list file")

# Create dict of all finalized ranks
tdList = {}
with open(final_ranks_filename, encoding='utf-8') as f:
    reader = DictReader(f)
    for attendee in reader:
        p = {}
        p['aga_id'] = attendee['OrganizationId']
        p['family_name'] = attendee['FamilyName']
        p['given_name'] = attendee['GivenName']
        unique_str = get_unique_string(p)
        tdList[unique_str] = get_rank_long(attendee['Rank'])

# Create dict for adhoc AGA ID info
adhoc_agaid = {}
with open(adhoc_filename, encoding='utf-8') as f:
    next(f)
    reader = DictReader(f)  
    for attendee in reader:
        adhoc_agaid[attendee['Full Name (Reversed)']] = attendee['Member Number']

# Create dict of all attendees to include their AGA rank
attendees = []
with open(registrant_filename, encoding='utf-8') as f:
    reader = DictReader(f)
    for attendee in reader:
        if (attendee['Status'] == 'Cancelled' or 
            attendee['Registrant Type'] == 'Non-Participant' or
            attendee['Registrant Type'] == 'Member Guest - Non-Participant'):
            continue
        p = {}
        p['family_name'] = attendee['Last Name']
        p['given_name'] = attendee['First Name']
        # p['aga_id'] = attendee['Member Number']
        p['aga_id'] = adhoc_agaid[p['family_name']+', '+p['given_name']]
        try:
            if attendee['Gender'] == 'Male':
                p['gender'] = 'm'
            elif attendee['Gender'] == 'Female':
                p['gender'] = 'f'
            else:
                p['gender'] = 'o'
        except:
            print(attendee['aga_id'], ' no gender')

        try:
            p['rank'] = tdList[get_unique_string(p)]
        except:
            tdList[get_unique_string(p)] = ''
            pass

        attendees.append(p)

        # if (attendee['Rating'] != 'Use AGA rating' and
        #     has_numbers(attendee['Rating']) and 
        #     attendee['Registrant Type'] != 'Non-Participant'):
        #     try:
        #         td_rank = tdList[p['aga_id']]
        #     except:
        #         td_rank = ''
        #     print(attendee['First Name'] + ',' + 
        #           attendee['Last Name'] + ',' +
        #           attendee['Member Number'] + ',' +
        #           td_rank + ','+
        #           attendee['Rating'])

# Write attendees dict to csv 
if os.path.exists(attendees_filename):
    os.remove(attendees_filename)
with open(attendees_filename, 'w', newline='') as attendees_csv:
    csv_columns = ['family_name', 'given_name', 'aga_id', 'gender', 'rank']
    writer = DictWriter(attendees_csv, fieldnames=csv_columns)
    writer.writeheader()
    writer.writerows(attendees)