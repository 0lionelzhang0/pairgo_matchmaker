# Automatic Pair Go Player List Generation

This Python script is used for parsing player Google Form signups, and automatically updating the Google Sheet player list. The 

The following three files are required for the program to run: 
- matchmaker.py
- credentials.json
- attendees.csv
Email the Go Congress registrar for them to export the csv containing the information of all attendees.
This csv should contain at least the following fields:
user_email
aga_id
family_name
given_name
alternate_name
phone
gender
rank

## Downloading credentials.json

![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/499f7dc9-6efc-4e1e-bdd9-c141e64d0995)

Create a new project with any name (e.g. "Pair Go").

Go to APIs & Services -> Credentials

![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/8f6f7b33-de19-4b05-987e-1ccb84a71838)

### OAuth Consent Screen

Choose External for consent screen

Pick a name for the app

Add your email to required fields

![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/32848e9d-454b-4189-84b3-41acc8663649)

Add these scopes

![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/83dd1da4-283b-452b-81f3-5d47e249ee36)

Add your email as a test user

### Gettings credentials.json

Go to Create Credentials -> OAuth client ID

![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/10cd5d72-cd0a-4ffe-a3be-82919ae842b4)

Download JSON and rename to credentials.json
