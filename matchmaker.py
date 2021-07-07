from __future__ import print_function
from enum import auto, unique
import os.path
from typing import Match
from fuzzywuzzy.fuzz import ratio
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from datetime import datetime
from fuzzywuzzy import process
import csv

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
TOURNAMENT_SPREADSHEET_ID = '11Esv5ezkFE92Ymak0ece5mPrP7pK4AWUEzzx1EwTKDM'
SIGNUP_SPREADSHEET_ID = '1hIXQZldciTIceMhnTTlBpkohDCY3z3O6gVPZPvoXq58'
STARTING_CELL = 'A5'
MISSING_LIST_CELL = 'I5'
STARTING_ROW = STARTING_CELL[1:]
TIME_CELL = 'A2'
STATS_CELL = 'F2'

class Matchmaker():
    def __init__(self):
        self.sheet = []
        self.player_sheet = 'Player List'
        self.attendee_list = []
        self.username_list = []
        self.attendee_unique_string_list = []
        self.attendee_aga_id_list = []
        self.pair_list = []
        self.partner_not_registered = 0
        self.looking_for_partner = 0
        self.debug_list = []
        self.get_credentials()

        # Email lists
        self.signed_up_but_not_registered = []
        self.registered_but_not_signed_up = []
        self.not_registered_for_pair_go = []

        # Parse congress registration
        with open('attendees.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for attendee in reader:
                username_igs = attendee['username_igs']
                if not attendee['cancelled']:
                    if username_igs:
                        # Avoid duplicates, new replaces old
                        if username_igs in self.username_list:
                            ind = self.username_list.index(username_igs)
                            self.attendee_list.pop(ind)
                            self.username_list.pop(ind)
                            self.attendee_unique_string_list.pop(ind)
                            self.attendee_aga_id_list.pop(ind)
                        attendee['rank_short'] = attendee['rank'][:-4] + attendee['rank'][-3]
                        attendee['rank_val'] = self.get_rank_val(attendee['rank_short'])
                        attendee['signed_up'] = False
                        attendee['paired'] = False

                        self.attendee_list.append(attendee)
                        self.username_list.append(username_igs)
                        self.attendee_unique_string_list.append(self.get_unique_string(attendee, 'attendee'))
                        self.attendee_aga_id_list.append(attendee['aga_id'])
                    else:
                        self.not_registered_for_pair_go.append(attendee['email'])
        print('Number of registered attendees: ', len(self.username_list))
        # Parse sign-ups
        self.signup_list = []
        self.signup_unique_string_list = []
        self.auto_pair_needed = 0
        resp = self.get(self.get_cell_string('2','420',sheet=''))
        for row in resp['values']:
            d = {}
            d['email'] = row[1]
            d['has_partner'] = True if row[2] == 'Yes' else False
            d['first_name'] = row[3]
            d['last_name'] = row[4]
            d['aga_id'] = row[5]
            d['min_pref'] = row[6]
            d['max_pref'] = row[7]
            d['partner_name'] = row[8] if d['has_partner'] else '' 
            d['partner_username'] = row[9] if d['has_partner'] else ''
            if not d['has_partner']:
                self.looking_for_partner += 1
            unique_str = self.get_unique_string(d, 'signup')
            ratios = process.extract(unique_str, self.signup_unique_string_list)
            if ratios and ratios[0][1] >= 95:
                ind = self.signup_unique_string_list.index(unique_str)
                self.signup_list.pop(ind)
                self.signup_unique_string_list.pop(ind)

            self.signup_list.append(d)
            self.signup_unique_string_list.append(unique_str)
        print('Number of sign-ups: ', len(self.signup_list))

        # Combine sign-ups with registration
        for s in self.signup_unique_string_list:
            signup_ind = self.signup_unique_string_list.index(s)
            
            aga_id = self.signup_list[signup_ind]['aga_id']
            ind = []
            if aga_id in self.attendee_aga_id_list:
                ind = self.attendee_aga_id_list.index(aga_id)
            else:
                ratios = process.extract(s, self.attendee_unique_string_list)
                if ratios[0][1] >= 90:
                    ind = self.attendee_unique_string_list.index(ratios[0][0])
            if ind:
                self.attendee_list[ind]['signup'] = self.signup_list[signup_ind]
                self.attendee_list[ind]['signed_up'] = True
            else:
                self.signed_up_but_not_registered.append(self.signup_list[signup_ind]['email'])

        for p in self.attendee_list:
            if p['signed_up']:
                if not p['signup']['has_partner']:
                    self.auto_pair_needed += 1
            else:
                self.registered_but_not_signed_up.append(p['email'])

        print('Number of registered and signed up people needing auto pair: ', self.auto_pair_needed, '\n')
        # print('Signed up but not registered: ', len(self.signed_up_but_not_registered))
        # self.display_emails(self.signed_up_but_not_registered)
        # print('Registered but not signed up: ', len(self.registered_but_not_signed_up))
        # self.display_emails(self.registered_but_not_signed_up)
        # print('Not registered for pair go: ', len(self.not_registered_for_pair_go))
        # self.display_emails(self.not_registered_for_pair_go)

        # print(self.debug_list)
    def display_emails(self, emails):
        str = ''
        for e in emails:
            str += e + ','
        str += '\n'
        print(str)

    def get_credentials(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)
        self.sheet = service.spreadsheets().values()

    def match_premade_pairs(self):
        for p_1 in self.attendee_list:
            if p_1['signed_up'] and not p_1['paired']:
                if p_1['signup']['has_partner']:
                    username = p_1['username_igs']
                    partner_username = p_1['signup']['partner_username']
                    ratios = process.extract(partner_username, self.username_list)
                    # print(partner_username)
                    # print(ratios)
                    if ratios[0][1] >= 95:
                        ind = self.username_list.index(ratios[0][0])
                        p_2 = self.attendee_list[ind]
                        self.add_pair_to_list(p_1, p_2, False)
                    else:
                        self.partner_not_registered += 1
                        
    def add_pair_to_list(self, p_1, p_2, auto_pair):


        
        pair = {}
        order = (p_1['gender'] == 'm')
        pair['male_player'] = p_1 if order else p_2
        pair['female_player'] = p_2 if order else p_1
        pair['auto_pair'] = 'Y' if auto_pair else 'N'
        pair['pair_points'] = self.get_pair_points(pair)

        if pair['female_player']['gender'] == 'm' and pair['pair_points'] > 4:
            return False

        self.pair_list.append(pair)
        p_1['paired'] = True
        p_2['paired'] = True
        if auto_pair:
            self.auto_pair_remaining -= 2
        return True

    def auto_match_pairs(self):
        # sum = 0
        # for p in self.attendee_list:
        #     if p['signed_up'] and not p['paired']:
        #         sum += 1
        # print(sum)

        auto_pair_list = []
        for p in self.attendee_list:
            if p['signed_up'] and not p['paired'] and not p['signup']['has_partner']:
                auto_pair_list.append(p)
                print(p['username_igs'] + ":" + p['rank_short'] + ':' + p['gender'] + ' ' + p['signup']['min_pref'] + ' to ' + p['signup']['max_pref'])
        auto_pair_list.sort(reverse=True, key=lambda p:p['rank_val'])

        n = 0
        self.auto_pair_remaining = self.auto_pair_needed
        while(self.auto_pair_remaining > 1 and n < 4):
            for p_1 in auto_pair_list:
                if not p_1['paired']:
                    # Non-male + male pairs
                    if p_1['gender'] != 'm':
                        for p_2 in auto_pair_list:
                            if p_2['gender'] == 'm' and not p_2['paired'] and p_2['username_igs'] != p_1['username_igs']:
                                if self.fit_pref_ranges(p_1, p_2, n):
                                    if self.add_pair_to_list(p_1, p_2, True):
                                        break
                    # Male + male pairs
                    else:
                        for p_2 in auto_pair_list:
                            if p_2['gender'] == 'm' and not p_2['paired'] and p_2['username_igs'] != p_1['username_igs']:
                                if self.fit_pref_ranges(p_1, p_2, n):
                                    if self.add_pair_to_list(p_1, p_2, True):
                                        break

            n += 1
            # print(self.auto_pair_remaining, n)

    def update_player_sheet(self):
        # self.update_time()
        self.update_stats()
        self.clear_all()
        self.pair_list.sort(reverse=True, key=self._sort)
        values = []
        n = 1
        for p in self.pair_list:
            v = []
            v.append(n)
            self.append_player_info(v, p['female_player'])
            self.append_player_info(v, p['male_player'])
            v.append(p['pair_points'])
            v.append(p['auto_pair'])
            values.append(v)
            n += 1
        self.update(self.get_cell_string(STARTING_CELL), values)
        self.update_missing_list()


    #------ Utility functions ------

    def get_pref_range_val(self, p, n):
        pref_range = list(range(self.get_rank_val(p['signup']['min_pref'])-n, self.get_rank_val(p['signup']['max_pref'])+1+n))
        # print(pref_range)
        return pref_range

    def fit_pref_ranges(self, p_1, p_2, n):
        if p_2['rank_val'] in self.get_pref_range_val(p_1, n):
            if p_1['rank_val'] in self.get_pref_range_val(p_2, n):
                return True
        return False

    def append_player_info(self, values, player):
        # if not player['anonymous']:
            # values.append(player['given_name'])
            # values.append(player['family_name'])
        values.append(player['username_igs'])
        # else:
        #     # values.append('Anonymous')
        #     # values.append('Anonymous')
        #     values.append('Anonymous')
        values.append(player['rank_short'])

    def get_pair_points(self, pair):
        m_rank = self.get_rank_val(pair['male_player']['rank_short'])
        f_rank = self.get_rank_val(pair['female_player']['rank_short'])
        return float(m_rank + f_rank) / 2.0

    def get_rank_val(self, rank):
        if rank[-1] == 'p' or rank == 'Professional':
            v = 10
        else:
            v = int(rank[:-1])
            if rank[-1] == 'k':
                v = -1 * v + 1
        return v

    def get_unique_string(self, d, case):
        str = ''
        if case == 'signup':
            str = d['first_name'].lower() + ' ' + d['last_name'].lower()# + ' ' + d['aga_id']
        elif case == 'attendee':
            str = d['given_name'].lower() + ' ' + d['family_name'].lower()# + ' ' + d['aga_id']
        return str

    def update_time(self):
        now = datetime.now()
        now = now.strftime('%m/%d/%Y %H:%M:%S')
        now = 'Last Updated\n\n' + now + ' PDT'
        self.update(self.get_cell_string(TIME_CELL), [[now]])

    def update_stats(self):
        now = datetime.now()
        now = now.strftime('%m/%d/%Y %H:%M:%S')
        now = 'Last Updated:\n' + now + ' PDT'
        stats = 'Registered: ' + str(len(self.username_list)) + '\n'
        # stats += 'Registered but hasn\'t filled form: ' + str(len(self.registered_but_not_signed_up)) + '\n'
        # stats += 'Filled form but hasn\'t registered: ' + str(len(self.signed_up_but_not_registered)) + '\n'
        # stats += 'Partner hasn\'t registered: ' + str(self.partner_not_registered) + '\n'
        stats += 'Looking for a partner: ' + str(self.auto_pair_needed) + '\n'
        stats += '\n'
        stats += now
        self.update(self.get_cell_string(STATS_CELL), [[stats]])

    def update_missing_list(self):
        missing_list = []
        for p in self.attendee_list:
            if not p['paired']:
                missing_list.append(p)
        missing_list.sort(key=lambda p: p['username_igs'].lower())
        values = []
        for p in missing_list:
            v = []
            v.append(p['username_igs'])
            if not p['signed_up']:
                v.append('N')
            elif p['signup']['has_partner']:
                v.append('Y')
                v.append('N')
            elif not p['signup']['has_partner']:
                v.append('Y')
                v.append('')
                v.append('N')
            values.append(v)
        self.update(self.get_cell_string(MISSING_LIST_CELL), values)

    def get_cell_string(self, a, b=None, sheet=None):
        if sheet is None:
            sheet = self.player_sheet
        if sheet:
            sheet += '!'
        str = sheet + a
        if b:
            str += ':' + b
        return str

    def clear_all(self):
        self.batch_clear(self.get_cell_string(STARTING_ROW, '420'))

    def _sort(self, p):
        return p['pair_points']

    #------ API Calls ------

    def batch_clear(self, ranges, spreadsheet_id=TOURNAMENT_SPREADSHEET_ID):
        body = {
            'ranges': [ranges]
        }
        resp = self.sheet.batchClear(spreadsheetId=spreadsheet_id, body=body).execute()
        return resp

    def append(self, values, range='A1:J1', value_input_option='RAW', insert_data_option='OVERWRITE', spreadsheet_id=TOURNAMENT_SPREADSHEET_ID):
        body = {
            'values': values
        }
        resp = self.sheet.append(spreadsheetId=spreadsheet_id, range=range, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=body).execute()
        return resp

    def update(self, range, values, value_input_option='RAW', spreadsheet_id=TOURNAMENT_SPREADSHEET_ID):
        body = {
            'values': values
        }
        resp = self.sheet.update(spreadsheetId=spreadsheet_id, range=range, body=body, valueInputOption=value_input_option).execute()
        return resp

    def get(self, range, spreadsheet_id=SIGNUP_SPREADSHEET_ID):
        resp = self.sheet.get(spreadsheetId=spreadsheet_id, range=range).execute()
        return resp

if __name__ == '__main__':
    m = Matchmaker()
    m.match_premade_pairs()
    m.auto_match_pairs()
    m.update_player_sheet()