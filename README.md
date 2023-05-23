# Automatic Pair Go Player List Generation

This Python script is used for parsing player Google Form signups, and automatically updating the Google Sheet player list. Note that the code and setup was originally only intended for my personal use, so the setup is not very refined. 

The following three files are required for the program to run: 
- matchmaker.py
  - This is the main Python script.
- credentials.json
  - This file contains your Google credentials so that the Python script can access Google Drive documents.
  - Instructions below on how to download.
- attendees.csv
  - Email the Go Congress registrar for them to export the csv containing the information of all attendees. This csv should contain at least the following fields:
    - user_email
    - aga_id
    - family_name
    - given_name
    - alternate_name
    - phone
    - gender
    - rank

# Running the tournament

Players should have the option to signup via Google Form or paper signups at the Go Congress. You will need to fill out a Google Form for any paper signups so having players fill the form themselves is preferable.

Once the one-time setup instructions below are completed, you may run the matchmaker.py script at any time to update the player list.

The script will look for the Google Form responses documents and update the player list on the Google Sheets "Official XXXX Pair Go Tournament".


# One-time Setup Instructions

## Downloading credentials.json

You can follow the [instructions provided by Google](https://developers.google.com/docs/api/quickstart/python)

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

## Running the main script

Make a copy of the [template files here](https://drive.google.com/drive/folders/1gv6l1rI5Mci498kiZeP2z3UkYQp-BQ2j?usp=sharing)

Be sure to change the places marked with Xs to the correct information.

Open the matchmaker.py and fill in the correct spreadsheet IDs, which can be found in the URL of the document.
Example:
![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/7da273de-b955-4132-92f8-def947697591)
![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/300945ef-d710-40ca-b710-f87895762c44)

### Setting up an IDE to run Python

1. Install [Visual Studio Code](https://code.visualstudio.com/Download)
2. Install [Python](https://www.python.org/downloads/)
3. Open the folder containing matchmaker.py in Visual Studio Code
4. Press Ctrl+Shift+P and seach for "Python: Create Environment" -> "Venv" -> Select installed Python version
5. Open the Terminal (View -> Terminal)
6. Try running the script and install missing packages in the terminal using
- "pip install [package_name]"
