import discord
from discord.ext import commands
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime, timedelta

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file("stlogistics-36de04f6404c.json", scopes=SCOPES)
client_gs = gspread.authorize(creds)

try:
    sheet = client_gs.open("41st Logistics").sheet1
except Exception as e:
    print("Error accessing the Google Sheet:", e)
    # Handle errors or exit if desired

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='write')
async def write_to_sheet(ctx, *, text: str):
    """
    Writes the provided text as a new entry in the Google Sheet.
    Usage: !write <text>
    """
    try:
        sheet.append_row([text])
        await ctx.send(f"Data '{text}' has been successfully written to the sheet.")
    except Exception as e:
        print("Error writing to Google Sheet:", e)
        await ctx.send(f"Could not write data to the sheet. Error: {e}")

@bot.command(name='loa_add')
async def loa_add(ctx, user: discord.Member, date_of_return: str = None):
    """
    Creates a Leave of Absence (LOA) entry for the mentioned user.
    Usage: !loa_add @user [optional_return_date]
    Defaults to two weeks from the current date if no return date is provided.
    """
    dol = datetime.now().strftime("%Y-%m-%d")
    dor = (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d") if not date_of_return else date_of_return
    nickname = user.display_name

    try:
        # Read column C (which is index 3) to see how many rows are occupied
        column_c_values = sheet.col_values(3)  # Column C
        rows_occupied = len(column_c_values)
        # Next row is row 4 minimum, or row (occupied + 1)
        next_row = max(rows_occupied + 1, 4)

        # Update cells in columns C, D, E (3,4,5) of next_row
        sheet.update_cell(next_row, 3, nickname)  # C
        sheet.update_cell(next_row, 4, dol)       # D
        sheet.update_cell(next_row, 5, dor)       # E

        await ctx.send(
            f"LOA entry added for {nickname}.\n"
            f"Date of Leave (DOL): {dol}\n"
            f"Date of Return (DOR): {dor}"
        )

    except Exception as e:
        print("Error writing LOA to Google Sheet:", e)
        await ctx.send(f"Could not write LOA entry to the sheet. Error: {e}")

@bot.command(name='loa_remove')
async def loa_remove(ctx, user: discord.Member):
    """
    Removes the LOA entry for the mentioned user if there is one.
    Usage: !loa_remove @user
    """
    nickname = user.display_name
    try:
        # Get all values in column C (user names) to see if there's a match
        column_c_values = sheet.col_values(3)  # Column C
        # Convert them to a list. If the user is found, find the row index
        # row_index = 1-based index in col_values, row_number = index as is.
        # But remember row_index=0 corresponds to the first returned cell (row 1).
        # So row_number = (index_in_list + 1)

        # Start searching at row 4. We can skip or slice column_c_values if needed.
        found = False
        for i, name in enumerate(column_c_values, start=1):
            if name.strip() == nickname and i >= 4:
                sheet.delete_rows(i)  # Delete the entire row
                found = True
                await ctx.send(f"LOA entry for {nickname} has been removed.")
                break

        if not found:
            await ctx.send(f"No LOA entry found for {nickname}.")

    except Exception as e:
        print("Error removing LOA from Google Sheet:", e)
        await ctx.send(f"Could not remove LOA entry. Error: {e}")

@bot.command(name='list_loa')
async def list_loa(ctx):
    """
    Lists all current LOA entries by reading columns C, D, E from row 4 onward.
    Usage: !list_loa
    """
    try:
        # Retrieve all data from the sheet or specifically from C4:E?
        # E.g. get_all_values() and then slice, or use range fetch:
        # The sheet might have unknown length, so let's get all values, then parse rows >= 4
        all_values = sheet.get_all_values()  # This gives a 2D array of the entire sheet

        # We'll gather rows that have data in columns C, D, E starting from row 4
        # row index in 2D array is row-1 (since indexing starts at 0)
        rows = []
        for row_index in range(3, len(all_values)):  # 3 means starting at "row 4" in human terms
            row_data = all_values[row_index]
            # Ensure the row has enough columns to include C(2), D(3), E(4)
            if len(row_data) < 5:
                continue
            nickname = row_data[2].strip()
            dol      = row_data[3].strip()
            dor      = row_data[4].strip()
            if nickname:  # if there's a user in col C
                rows.append((nickname, dol, dor))

        if not rows:
            await ctx.send("No one is currently on LOA.")
            return

        # Create a formatted list output
        message_lines = ["**Current LOA Entries**:"]
        for idx, (nickname, dol, dor) in enumerate(rows, start=1):
            message_lines.append(f"{idx}. **{nickname}** | DOL: {dol} -> DOR: {dor}")

        await ctx.send("\n".join(message_lines))

    except Exception as e:
        print("Error listing LOAs:", e)
        await ctx.send(f"Could not list LOA entries. Error: {e}")

def get_bot_token():
    with open('Bot-Token.txt', 'r') as file:
        return file.read().strip()

bot.run(get_bot_token())
