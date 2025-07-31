# 41st_web-bot-
41st_web bot 
# 41st Web Bot

This repository contains a simple Discord bot to handle Leave of Absence (LOA) requests and store them in a Google Sheet.

## Setup

1. Create the following files in the project directory (do not commit real keys):
   - `discord_token.txt` &ndash; contains your Discord bot token.
   - `google_creds.json` &ndash; Google service account credentials for `gspread`.
   - `sheet_id.txt` &ndash; the ID of the Google Sheet where LOA entries will be stored.
   - `exloa_channel_id.txt` &ndash; ID of the channel to receive extended LOA messages (optional).

2. Install dependencies:
   ```bash
   pip install discord.py gspread oauth2client
   ```

3. Run the bot:
   ```bash
   python loa_bot.py
   ```

## Commands

- `!LOA @user duration`

  Records an LOA for `@user`. Duration is specified in weeks and days (maximum 2 weeks). Example:

  ```
  !LOA @sykles 1week 2days
  ```

- `!exLOA @user duration`

  Same as `!LOA` but the bot will prompt for an additional message. The message is sent to the channel specified in `exloa_channel_id.txt`.

LOA entries are appended to the Google Sheet with the user name, the start date and calculated return date in `dd.mm.yyyy` format.
