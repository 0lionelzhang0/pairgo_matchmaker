from __future__ import print_function
from enum import auto, unique
import os
from re import T
from typing import Match
from fuzzywuzzy.fuzz import ratio
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from datetime import datetime
from fuzzywuzzy import process
import csv
import time
import copy

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
TOURNAMENT_SPREADSHEET_ID = '1uMzzTHt10VbPc_HgWbO2K0-_BSwy17DYLxLHQ0TGnrs'
SIGNUP_SPREADSHEET_ID = '1H8e-PwCmGM8Dxe4UQX7LxitZ2-_vj8-jNWsLv-hoapE'
STARTING_CELL = 'A5'
MAIN_EVENT_STARTING_CELL = 'A9'
MISSING_LIST_CELL = 'I5'
STARTING_ROW = STARTING_CELL[1:]
STATS_CELL = 'F2'

class Matchmaker():
    def __init__(self):
        self.sheet = []
        self.player_sheet = 'Player List'
        self.attendee_list = []
        self.signed_up_but_not_registered_list = []
        # self.username_list = []
        self.attendee_unique_string_list = []
        self.attendee_aga_id_list = []
        self.pair_list = []
        self.iapgc_pair_list = []
        self.partner_not_registered = 0
        self.looking_for_partner = 0
        self.debug_list = []
        self.get_credentials()

        # Email lists
        self.signed_up_but_not_registered_emails = []
        self.registered_but_not_signed_up = []
        self.not_registered_for_pair_go = []
        self.not_registered_females = []

        # Parse congress registration
        with open('attendees.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for attendee in reader:
                
                if not attendee['cancelled'] and attendee['rank'] != 'Non-player':
                    # if username_igs:
                        # Avoid duplicates, new replaces old
                        # if username_igs in self.username_list:
                        #     ind = self.username_list.index(username_igs)
                        #     self.attendee_list.pop(ind)
                        #     self.username_list.pop(ind)
                        #     self.attendee_unique_string_list.pop(ind)
                        #     self.attendee_aga_id_list.pop(ind)
                    attendee['aga_id'] = attendee['aga_id'] if attendee['aga_id'] else 0
                    attendee['rank_short'] = attendee['rank'][:-4] + attendee['rank'][-3]
                    attendee['rank_val'] = self.get_rank_val(attendee['rank_short'])
                    attendee['signed_up'] = False
                    attendee['paired'] = False
                    attendee['given_name'] = attendee['given_name'].rstrip()
                    attendee['family_name'] = attendee['family_name'].rstrip()
                    self.attendee_list.append(attendee)
                    self.attendee_unique_string_list.append(self.get_unique_string(attendee, 'attendee'))
                    self.attendee_aga_id_list.append(attendee['aga_id'])
                    # else:
                    #     self.not_registered_for_pair_go.append(attendee['email'])
                    #     if attendee['gender'] == 'f':
                    #         self.not_registered_females.append(attendee['email'])

        print('Number of registered attendees: ', len(self.attendee_list))

        # Parse sign-ups
        self.signup_list = []
        self.signup_unique_string_list = []
        self.auto_pair_needed = 0
        resp = self.get(self.get_cell_string('2','420',sheet=''))
        print(resp)
        for row in resp['values']:
            try:
                d = {}
                d['email'] = row[1]
                d['given_name'] = row[2].rstrip()
                d['family_name'] = row[3].rstrip()
                d['aga_id'] = row[4]
                d['has_partner'] = True if row[5] == 'Yes' else False
                if d['has_partner']:
                    d['partner_given_name'] = row[6]
                    d['partner_family_name'] = row[7]
                    d['partner_aga_id'] = row[8]
                    d['iapgc'] = True if row[12] == 'Yes' and d['aga_id'] and d['partner_aga_id'] else False
                else:
                    d['min_pref'] = row[9]
                    d['max_pref'] = row[10]
                    d['waitlist'] = True if row[11] == 'Yes' else False
                    d['iapgc'] = False
                
                if not d['has_partner']:
                    self.looking_for_partner += 1
            except Exception as e:
                print('skipped: ', row[2], ' ', row[3])
                print(e)
                continue
            unique_str = self.get_unique_string(d, 'attendee')
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
            ind = None
            if aga_id and aga_id in self.attendee_aga_id_list:
                ind = self.attendee_aga_id_list.index(aga_id)
            else:
                ratios = process.extract(s, self.attendee_unique_string_list)
                if ratios[0][1] >= 90:
                    ind = self.attendee_unique_string_list.index(ratios[0][0])
            if not ind is None:
                self.attendee_list[ind]['signup'] = self.signup_list[signup_ind]
                self.attendee_list[ind]['signed_up'] = True
            else:
                self.signed_up_but_not_registered_emails.append(self.signup_list[signup_ind]['email'])
                self.signed_up_but_not_registered_list.append(self.signup_list[signup_ind])

        for p in self.attendee_list:
            if p['signed_up']:
                if not p['signup']['has_partner']:
                    self.auto_pair_needed += 1

    def debug(self):
        resp = self.get(self.get_cell_string('2','420',sheet='Check-in Responses'), spreadsheet_id=TOURNAMENT_SPREADSHEET_ID)
        print(resp)

    def display_all_emails(self):
        for p in self.attendee_list:
            if not p['signed_up'] and not p['paired']:
                self.registered_but_not_signed_up.append(p['email'])

        resp = self.get(self.get_cell_string('2','420',sheet='Check-in Responses'), spreadsheet_id=TOURNAMENT_SPREADSHEET_ID)

        all_players = []
        not_checked_in = []
        not_checked_in_singles = []
        for p in self.attendee_list:
            if p['paired'] or p['signed_up']:
                all_players.append(p['email'])
                checked_in = False
                for row in resp['values']:
                    if p['username_igs'].lower() == row[1].lower():
                        checked_in = True
                        break
                if not checked_in:
                    not_checked_in.append(p['email'])
                    if p['signed_up'] and not p['signup']['has_partner']:
                        not_checked_in_singles.append(p['email'])

        print('Number of registered and signed up people needing auto pair: ', self.auto_pair_needed, '\n')
        print('Signed up but not registered: ', len(self.signed_up_but_not_registered_emails))
        self.display_emails(self.signed_up_but_not_registered_emails)
        print('Registered but not signed up: ', len(self.registered_but_not_signed_up))
        self.display_emails(self.registered_but_not_signed_up)
        # print('Not registered for pair go: ', len(self.not_registered_for_pair_go))
        # self.display_emails(self.not_registered_for_pair_go)
        # print('Not registered females: ', len(self.not_registered_females))
        # self.display_emails(self.not_registered_females)
        print('All paired and signed up players: ', len(all_players))
        self.display_emails(all_players)
        print('Not checked in: ', len(not_checked_in))
        self.display_emails(not_checked_in)
        print('Not checked in singles: ', len(not_checked_in_singles))
        self.display_emails(not_checked_in_singles)

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
                try:
                    creds.refresh(Request())
                except:
                    os.remove('token.json')
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)
        self.sheet = service.spreadsheets()

    def match_premade_pairs(self):
        for p_1 in self.attendee_list:
            if p_1['signed_up'] and not p_1['paired']:
                if p_1['signup']['has_partner']:
                    partner_unique_str = self.get_unique_string(p_1['signup'], 'partner')
                    ratios = process.extract(partner_unique_str, self.attendee_unique_string_list)
                    if ratios[0][1] >= 95:
                        ind = self.attendee_unique_string_list.index(ratios[0][0])
                        p_2 = self.attendee_list[ind]
                        if p_2['paired']:
                            print(partner_unique_str, 'Already paired')
                        else:
                            self.add_pair_to_list(p_1, p_2, auto_pair=False, iapgc=p_1['signup']['iapgc'])
                    else:
                        self.partner_not_registered += 1

    def auto_match_pairs(self):
        t = time.time()
        n = 0

        # Calculate number of matches per player
        auto_pair_list = []
        for p in self.attendee_list:
            if p['signed_up'] and not p['paired'] and not p['signup']['has_partner']:
                auto_pair_list.append(p)
        auto_pair_list.sort(key=lambda p: (p['gender'], -p['rank_val']))
        n_female = 0
        for p_1 in auto_pair_list:
            if p_1['gender'] == 'f':
                n_female += 1
            p_1['num_matches'] = 0
            p_1['matches'] = []
            for p_2 in auto_pair_list:
                p_1_str = self.get_unique_string(p_1, 'attendee')
                p_2_str = self.get_unique_string(p_2, 'attendee')
                if p_1_str != p_2_str:
                    if self.is_compatible_pair(p_1, p_2, n):
                        p_1['num_matches'] += 1
                        p_1['matches'].append(p_2)
            # Sort matches by closest rank
            p_1['matches'].sort(key=lambda i: (abs(i['rank_val']-p_1['rank_val'])))
        print('Number of females looking for partner: ', n_female)
        for p in auto_pair_list[:]:
            if p['num_matches'] == 0 or p['paired']:
                auto_pair_list.remove(p)
        
        # Iteratively pair up players
        while auto_pair_list:
            auto_pair_list.sort(key=lambda p: p['num_matches'])
            # for p in auto_pair_list:
            #     print(p['username_igs'] + ":" + p['rank_short'] + ':' + p['gender'] + ' ' + p['signup']['min_pref'] + ' to ' + p['signup']['max_pref'] + ' matches:' + str(p['num_matches']))
            #     for i in p['matches']:
            #         print(i['username_igs'])
            p = auto_pair_list[0]
            p_2 = p['matches'][0]
            self.add_pair_to_list(p, p_2, True)
            for k in [p, p_2]:
                for i in k['matches']:
                    i['num_matches'] -= 1
                    for j in i['matches'][:]:
                        j_str = self.get_unique_string(j, 'attendee')
                        k_str = self.get_unique_string(k, 'attendee')
                        if j_str == k_str:
                            i['matches'].remove(j)
                            break
            for p in auto_pair_list[:]:
                if p['num_matches'] == 0 or p['paired']:
                    auto_pair_list.remove(p)

        elapsed = time.time() - t
        print('Time elapsed: ', str(elapsed))

    def update_checkin_status(self):
        requests = []
        for row in range(4,421):
            for col in [1,3]:
        # for row in [11]:
        #     for col in [2]:
                ranges = {
                    'sheetId': 1995723187, #200277502 is testing, 1995723187 is player sheet
                    'startRowIndex': row,
                    'endRowIndex': row+1,
                    'startColumnIndex': col,
                    'endColumnIndex': col+1,
                }
                requests = self.add_conditional_format(requests, ranges)
        self.update_format([requests])

    def update_player_sheet(self):
        self.update_stats()
        self.clear_all()
        self.iapgc_pair_list.sort(reverse=True, key=self._sort)
        n = 1
        n_iapgc = len(self.iapgc_pair_list)

        if n_iapgc > 4:
            for i in range(4, n_iapgc):
                self.pair_list.append(self.iapgc_pair_list[i])

        iapgc_values = []
        for i in range(min(n_iapgc, 4)):
            p = self.iapgc_pair_list[i]
            v = []
            v.append(n)
            self.append_player_info(v, p['female_player'])
            self.append_player_info(v, p['male_player'])
            v.append(p['pair_points'])
            v.append(p['auto_pair'])
            iapgc_values.append(v)
            n += 1
        self.update(self.get_cell_string(STARTING_CELL), iapgc_values)

        self.pair_list.sort(reverse=True, key=self._sort)
        values = []
        for p in self.pair_list:
            v = []
            v.append(n)
            self.append_player_info(v, p['female_player'])
            self.append_player_info(v, p['male_player'])
            v.append(p['pair_points'])
            v.append(p['auto_pair'])
            values.append(v)
            n += 1
        self.update(self.get_cell_string(MAIN_EVENT_STARTING_CELL), values)
        self.update_missing_list()

    #------ Utility functions ------

    def add_pair_to_list(self, p_1, p_2, auto_pair, iapgc=False):
        pair = {}
        order = (p_1['gender'] == 'm')
        pair['male_player'] = p_1 if order else p_2
        pair['female_player'] = p_2 if order else p_1
        pair['auto_pair'] = 'Y' if auto_pair else 'N'
        pair['pair_points'] = self.get_pair_points(pair)
        if iapgc:
            self.iapgc_pair_list.append(pair)
        else:
            self.pair_list.append(pair)
        p_1['paired'] = True
        p_2['paired'] = True

    def get_pref_range_val(self, p, n):
        min = self.get_rank_val(p['signup']['min_pref'])
        max = self.get_rank_val(p['signup']['max_pref'])
        if min > max:
            min, max = max, min
        pref_range = list(range(min-n, max+1+n))
        return pref_range

    def is_compatible_pair(self, p_1, p_2, n):
        if p_1['gender'] == 'f' and p_2['gender'] == 'f':
            return False
        if p_1['gender'] == 'm' and p_2['gender'] == 'm':
            return False
        if p_2['rank_val'] not in self.get_pref_range_val(p_1, n):
            return False
        if p_1['rank_val'] not in self.get_pref_range_val(p_2, n):
            return False
        # if self.get_pair_points({'male_player':p_1, 'female_player':p_2}) >= 4 and p_1['gender'] == 'm' and p_2['gender'] == 'm':
        #     return False
        return True

    def append_player_info(self, values, player):
        values.append(player['given_name'].title() + ' ' + player['family_name'].title())
        values.append(player['rank_short'])

    def get_pair_points(self, pair):
        m_rank = self.get_rank_val(pair['male_player']['rank_short'])
        f_rank = self.get_rank_val(pair['female_player']['rank_short'])
        return float(m_rank + f_rank) / 2.0

    def get_rank_val(self, rank):
        if rank[-1] == 'p' or rank == 'Professional':
            v = 8
        else:
            v = int(rank[:-1])
            if rank[-1] == 'k':
                v = -1 * v + 1
        return v

    def get_unique_string(self, d, case):
        string = ''
        if case == 'partner':
            string = d['partner_given_name'].lower() + ' ' + d['partner_family_name'].lower() + ' ' + str(d['partner_aga_id'])
        elif case == 'attendee':
            string = d['given_name'].lower() + ' ' + d['family_name'].lower() + ' ' + str(d['aga_id'])
        return string

    def update_stats(self):
        now = datetime.now()
        now = now.strftime('%m/%d/%Y %H:%M:%S')
        now = 'Last Updated:\n' + now + ' PDT'
        stats = 'Registered: ' + str(len(self.signup_list)) + '\n'
        stats += 'Looking for a partner: ' + str(self.auto_pair_needed) + '\n'
        stats += '\n'
        stats += now
        self.update(self.get_cell_string(STATS_CELL), [[stats]])

    def update_missing_list(self):
        missing_list = []
        for p in self.attendee_list:
            if p['signed_up'] and not p['paired']:
                missing_list.append(p)
        # missing_list.sort(key=lambda p: self.get_unique_string(p, 'attendee'))
        missing_list.sort(key=lambda p: -p['rank_val'])

        values = []
        for p in missing_list:
            v = []
            v.append(p['given_name'] + ' ' + p['family_name'])
            v.append(p['rank_short'])
            
            if p['signup']['has_partner']:
                v.append('Y')
                v.append('N')
            elif not p['signup']['has_partner']:
                v.append('Y')
                v.append('')
                v.append('N')
            values.append(v)

        for p in self.signed_up_but_not_registered_list:
            v = []
            v.append(p['given_name'] + ' ' + p['family_name'])
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
        resp = self.sheet.values().batchClear(spreadsheetId=spreadsheet_id, body=body).execute()
        return resp

    def append(self, values, range='A1:J1', value_input_option='RAW', insert_data_option='OVERWRITE', spreadsheet_id=TOURNAMENT_SPREADSHEET_ID):
        body = {
            'values': values
        }
        resp = self.sheet.values().append(spreadsheetId=spreadsheet_id, range=range, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=body).execute()
        return resp

    def update(self, range, values, value_input_option='RAW', spreadsheet_id=TOURNAMENT_SPREADSHEET_ID):
        body = {
            'values': values
        }
        resp = self.sheet.values().update(spreadsheetId=spreadsheet_id, range=range, body=body, valueInputOption=value_input_option).execute()
        return resp

    def get(self, range, spreadsheet_id=SIGNUP_SPREADSHEET_ID):
        resp = self.sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        return resp

    def add_conditional_format(self, requests, _range):
        col = chr(_range['startColumnIndex'] + 65)
        row = str(_range['startRowIndex'] + 1)
        cell = col + row

        # formula = ['=exact(vlookup(' + cell + ',indirect("Check-in Responses!B:D"),2,0),"Yes")',
        #            '=exact(vlookup(' + cell + ',indirect("Check-in Responses!B:D"),2,0),"No")']
        formula = ['=EXACT(INDEX(indirect("Check-in Responses!B:D"), MAX(filter(ROW(indirect("Check-in Responses!B:B")), indirect("Check-in Responses!B:B")='+cell+')),2),"Yes")',
                   '=EXACT(INDEX(indirect("Check-in Responses!B:D"), MAX(filter(ROW(indirect("Check-in Responses!B:B")), indirect("Check-in Responses!B:B")='+cell+')),2),"No")']
        color = [{
                    'red': 0.85,
                    'green': 0.917647,
                    'blue': 0.82745
                },
                {
                    'red': 0.95686,
                    'green': 0.7804,
                    'blue': 0.7647
                }]

        # formula = '=match(' + cell + ',indirect("Check-in Responses!B:B"),0)'
        for i in range(2):
            rule = {'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [_range],
                        'booleanRule': {
                            'condition': {
                                'type': 'CUSTOM_FORMULA',
                                'values': [{
                                    'userEnteredValue':
                                        formula[i]
                                }]
                            },
                            'format': {
                                'backgroundColor': color[i]
                            }
                        }
                    },
                    'index': 0
                }
            }
            requests.append(rule)
        return requests


    def update_format(self, requests, spreadsheet_id=TOURNAMENT_SPREADSHEET_ID):
        body = {
            'requests': requests
        }
        response = self.sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


if __name__ == '__main__':
    m = Matchmaker()
    # m.debug()
    m.match_premade_pairs()
    m.auto_match_pairs()
    # m.update_checkin_status()
    m.update_player_sheet()
    # m.display_all_emails()