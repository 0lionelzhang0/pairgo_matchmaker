# Automatic Pair Go Player List Generation

This Python script is used for parsing player Google Form signups, and automatically updating the Google Sheet player list. Note that the code and setup was originally only intended for my personal use, so the setup is not very refined. 

|   | Tutorial                                                                        | Description                                        |
|---|---------------------------------------------------------------------------------|----------------------------------------------------|
| 1 | [Tournament Basics](tournament_basics.md)                                       | Basic rules and format of the pair go tournament |
| 2 | [One-time Setup Instructions](setup_instructions.md)                            | Setup instructions running the matchmaking script |
| 3 | [Teleoperating Stretch](teleoperating_stretch.md)                               | Control Stretch with a keyboard or xbox controller |


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




### Setting up an IDE to run Python

1. Install [Visual Studio Code](https://code.visualstudio.com/Download)
2. Install [Python](https://www.python.org/downloads/)
3. Open the folder containing matchmaker.py in Visual Studio Code
4. Press Ctrl+Shift+P and seach for "Python: Create Environment" -> "Venv" -> Select installed Python version
5. Open the Terminal (View -> Terminal)
6. Try running the script and install missing packages in the terminal using
- "pip install [package_name]"
