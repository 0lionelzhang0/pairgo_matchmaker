## Running the tournament

### Overview of registration pipeline

Players should have the option to signup via Google Form or paper signups at the Go Congress. You will need to fill out a Google Form for any paper signups so having players fill the form themselves is preferable.

These Google Form responses will be collected in a Google Sheet with the name "XXXX Pair Go Sign-up Form (Responses)".

When matchmaker.py is run, the script will look at the Google Form responses and verify their registration in the attendees.csv file. Verified pairs will be updated to the primary Google Sheet titled "Official XXXX Pair Go Tournament". Players that are looking for a partner and not matched yet will appear on the right. The columns on the right will also indicate if the player or their partner is not yet registered for the Go Congress. Note that sometimes this may be due to typos.

![image](https://github.com/0lionelzhang0/pairgo_matchmaker/assets/36424267/4376afa0-173a-419c-9e77-8871a91bb22f)


Once the one-time setup instructions below are completed, you may run the matchmaker.py script at any time to update the player list.

The script will look for the Google Form responses documents and update the player list on the Google Sheets "Official XXXX Pair Go Tournament".
