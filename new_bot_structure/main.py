import os
import subprocess
import discord
from database import *
from utils import *

from discord import user
from discord.ext import commands
from datetime import datetime
import pandas as pd
import sqlite3
import asyncio
import re
import time
import random
from datetime import timedelta
# main.py


# Variable to store the state of automatic credit updating
auto_update_enabled = False
debug_mode_enabled = False

from discord.ext.commands import CommandInvokeError


# Define the rewards based on roles
rewards = {
    "Art Team": ["Bad Batch Echo helmet"],
    "Art Team Veteran": ["Store Items for 10k and under are free"],
    "Clone Trooper": ["white and green colour on the helmet"],
    "Veteran Trooper": ["camouflage and grey on the helmet"],
    "Sergeant": ["Rangefinder", "tiny amount of extra colour (no pink and gold)"],
    "2nd Lieutenant": ["Custom Visor (no gold, white and pink)", "small amount of extra colour (no gold)"],
    "Lieutenant": ["Custom Visor (no gold, white and pink)", "small amount of extra colour (no gold)"],
    "Captain": ["Halfbody", "Custom Visor can be gold/pink", "gold on the armour"],
    "Major": ["Halfbody", "Custom Visor can be gold/pink", "gold on the armour"],
    "Technical Commander": ["Halfbody", "Custom Visor can be gold/pink", "gold on the armour"],
    "High Command": ["Visor Glow", "white visor"],
    "ARC Trooper": ["decent amount of extra colour", "green still has to be the main colour"],
    "Republic Commando": ["decent amount of extra colour", "green still has to be the main colour"]
}


# Function to get the rewards based on user roles




# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Enable reading message content
intents.members = True  # Enable members intent

bot = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)

async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename}")
            except Exception as e:
                print(f"Failed to load Cog {filename}: {e}")

bot.setup_hook = setup_hook


# Dictionary to store credits (used for real-time tracking)
credits_dict = {}

# Initialize role_credits from the database
role_credits = {role: credits for role, credits in get_all_role_credits()}
non_stacking_roles = {role: credits for role, credits in get_all_non_stacking_role_credits()}

role_credits = dict(get_all_role_credits())
non_stacking_role_credits = dict(get_all_non_stacking_role_credits())

# Function to read a file and return its contents
# Function to read a file and return its contents


# Channels where the bot commands are allowed
ALLOWED_CHANNEL_NAMES = ['bot-test', 'bot-commands']
REPORT_CHANNEL_NAME = 'bug-reports'


# Google Sheets setup

# Function to read a file and return its contents


# Ensure continuous operation
async def keep_active():
    while True:
        await asyncio.sleep(3600)  # Keeps the loop running every hour




@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    for guild in bot.guilds:
        for member in guild.members:
            db_credits = get_user_credits(member.id, member.roles, role_credits, non_stacking_roles)
            if db_credits and len(db_credits) == 3:
                current_credits, max_credits, removed_credits = db_credits
            else:
                current_credits = 0
                max_credits = 0
                removed_credits = 0

            regular_credits = sum(role_credits.get(role.name, 0) for role in member.roles if role.name in role_credits)
            max_non_stacking_credit = max(
                (non_stacking_roles.get(role.name, 0) for role in member.roles if role.name in non_stacking_roles),
                default=0)

            total_credits = regular_credits + max_non_stacking_credit
            total_credits += current_credits - regular_credits - max_non_stacking_credit

            if current_credits != total_credits:
                update_user_credits(member.id, total_credits)
                credits_dict[member.id] = total_credits
                print(f'Updated credits for member {member.id}: {total_credits}')
            else:
                credits_dict[member.id] = current_credits

    # Send startup message to bot-commands channel
    startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    version = ("1.7 ~ Purchase")
    embed = discord.Embed(
        title="Bot Startup",
        description=f"The bot has started successfully.\n\n**Startup Time:** {startup_time}\n**Version:** {version}",
        color=discord.Color.red()
    )
    channel = discord.utils.get(bot.get_all_channels(), name='bot-commands')
    if channel:
        await channel.send(embed=embed)

    bot.loop.create_task(keep_active())  # Start the keep active task


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # 1) Rollen als Sets von Namen erfassen
    before_roles = {role.name for role in before.roles}
    after_roles  = {role.name for role in after.roles}

    # 2) Hinzugekommene und entfernte Rollen in Namensform
    removed_roles = before_roles - after_roles
    added_roles   = after_roles - before_roles

    # 3) IDs der Server, auf denen Rollen persistent sein k�nnen
    server_ids = [850840453800919100, 1138926753931346090, 911409562970628167]

    if removed_roles or added_roles:
        # 4) Aktuellen Credit-Stand aus der DB holen
        db_credits = get_user_credits(after.id, after.roles, role_credits, non_stacking_roles)
        current_credits = db_credits[0] if db_credits else 0

        print(f"Current credits for user {after.id}: {current_credits}")
        print(f"Removed roles: {removed_roles}")
        print(f"Added roles:   {added_roles}")

        # 5) Removed Credits berechnen (nur stackable Roles)
        removed_credits = 0
        for role_name in removed_roles:
            if role_name in role_credits:
                # Pr�fen, ob der User die Rolle noch auf einem anderen Server hat
                has_elsewhere = False
                for sid in server_ids:
                    if sid != before.guild.id:
                        roles_elsewhere = get_user_roles_from_servers(after.id, [sid])
                        if role_name in roles_elsewhere:
                            has_elsewhere = True
                            break
                if not has_elsewhere:
                    removed_credits += role_credits[role_name]
                    unmark_role_credited(after.id, role_name)
                    print(f"Unmarking role {role_name} as credited for user {after.id}")
        print(f"Removed credits: {removed_credits}")

        # 6) Added Credits berechnen (nur stackable Roles, nur neue)
        added_credits = 0
        for role_name in added_roles:
            if role_name in role_credits:
                if not check_role_credited(after.id, role_name):
                    added_credits += role_credits[role_name]
                    mark_role_credited(after.id, role_name)
                    print(f"Marking role {role_name} as credited for user {after.id}")
                else:
                    print(f"Role {role_name} already credited for user {after.id}")
        print(f"Added credits: {added_credits}")

        # 7) Non-Stacking: Maximalwert vor und nach dem Update
        max_before = max((non_stacking_roles.get(r, 0) for r in before_roles), default=0)
        max_after  = max((non_stacking_roles.get(r, 0) for r in after_roles), default=0)
        print(f"Max before non-stacking credit: {max_before}")
        print(f"Max after non-stacking credit:  {max_after}")

        # Warnung, wenn eine niedrigere Non-Stacking-Role hinzugef�gt wurde
        for role_name in added_roles:
            if role_name in non_stacking_roles and non_stacking_roles[role_name] < max_before:
                print(
                    f"Non-stacking role {role_name} added but gives no credits "
                    f"because user {after.id} already has a higher one"
                )

        # 8) Neue Gesamt-Credits berechnen & updaten
        new_credits = current_credits - removed_credits + added_credits + (max_after - max_before)
        print(f"New credits calculation: {new_credits}")

        print(f"Updating user credits: user_id={after.id}, new_credits={new_credits}")
        update_user_credits(after.id, new_credits)
        credits_dict[after.id] = new_credits
        print(f"Updated credits for member {after.id}: {new_credits}")


def add_or_update_user(member):
    user_id = member.id
    current_credits = 0
    max_credits = 0
    removed_credits = 0

    # Calculate total credits from roles
    role_credits_sum = sum(role_credits.get(role.name, 0) for role in member.roles if role.name in role_credits)
    max_non_stacking_credit = max(
        (non_stacking_roles.get(role.name, 0) for role in member.roles if role.name in non_stacking_roles), default=0)
    total_credits = role_credits_sum + max_non_stacking_credit

    # Connect to the database
    connection = sqlite3.connect('credits.db')
    cursor = connection.cursor()

    # Check if user already exists in the database
    cursor.execute('SELECT user_id FROM user_credits WHERE user_id = ?', (user_id,))
    data = cursor.fetchone()

    if data:
        # User exists, update their credits
        cursor.execute('UPDATE user_credits SET current_credits = ?, max_credits = ? WHERE user_id = ?',
                       (total_credits, total_credits, user_id))
        print(f'Updated credits for existing user {user_id}: {total_credits}')
    else:
        # User does not exist, add them with calculated credits
        cursor.execute(
            'INSERT INTO user_credits (user_id, current_credits, max_credits, removed_credits) VALUES (?, ?, ?, ?)',
            (user_id, total_credits, total_credits, removed_credits))
        print(f'Added new user {user_id} with credits: {total_credits}')

    # Commit the transaction and close the connection
    connection.commit()
    connection.close()


updated_users = set()


@bot.event
async def on_message(message):
    print("on_message event triggered.")  # Debug: Event triggered
    print(f"Received message from {message.author.name}: {message.content}")  # Debug: Message received

    # Check if the message is from a guild channel
    if isinstance(message.channel, discord.DMChannel):
        print("Message is from a DM channel, ignoring.")  # Debug: DM Channel
        return

    # Process commands as usual
    await bot.process_commands(message)

    # Check if the message is in the 'bot-commands' channel for specific processing
    if message.channel.name not in ALLOWED_CHANNEL_NAMES:
        print("Message is not in the allowed channel.")  # Debug: Wrong channel
        return

    # Check if the message is from '41st Utilities'
    if message.author.name == "41st Utilities":
        print("Message is from '41st Utilities'.")  # Debug: Command check

        # Check if the message has embeds
        if message.embeds:
            print("Message contains embeds.")  # Debug: Embed check
            embed = message.embeds[0]
            embed_dict = embed.to_dict()
            print(f"Embed content: {embed_dict}")  # Debug: Embed content

            try:
                # Extract user mention from the embed
                description = embed_dict.get('description', '')
                print(f"Embed description: {description}")  # Debug: Embed description
                if description:
                    user_mention = description.split()[0]
                    print(f"User mention found in embed: {user_mention}")  # Debug: User mention in embed
                else:
                    user_mention = None
                    print("No user mention found in the embed.")  # Debug: User mention not found

                # Extract credit value from the embed description with markdown handling
                credit_value_match = re.search(r'`(\d+)`', description)
                if credit_value_match:
                    credit_value = int(credit_value_match.group(1))
                    print(f"Credit value extracted from embed: {credit_value}")  # Debug: Credit value in embed
                else:
                    print("No credit value found in the embed.")  # Debug: Credit value not found in embed
                    return

                if user_mention:
                    # Extract the user ID from the mention
                    user_id = int(re.findall(r'\d+', user_mention)[0])
                    print(f"Extracted user ID: {user_id}")  # Debug: Extracted user ID

                    # Fetch the member object to get roles
                    member = message.guild.get_member(user_id)
                    if not member:
                        print(f"Member with ID {user_id} not found in the guild.")
                        return

                    # Debug information, no update
                    print(f"User {user_id} would have credits updated to {credit_value}, but this action is disabled.")

            except Exception as e:
                print(f"Error processing .credits command from embed: {e}")  # Debug: Exception
        else:
            print("Message does not contain embeds.")  # Debug: No embed
            print("No user mention found in the message.")  # Debug: User mention missing
            print("No credit value found in the message.")  # Debug: Credit value missing
    else:
        print("Message is not from '41st Utilities'.")  # Debug: Command not matched

    print("Processed commands.")  # Debug: Processed commands




# Lade die Medaillen in ein Dictionary
medals = read_medals('Regiment medals python.txt')


# Function to add a medal to a user and update their credits


# Function to remove a medal from a user and update their credits






# Function to get user roles from servers


# List of server IDs to check
server_ids = [850840453800919100, 1138926753931346090, 911409562970628167]








bot.remove_command('help')










# Start troll commands













# Note: You can get the user's ID by enabling Developer Mode in Discord,
# right-clicking on the user, and selecting "Copy ID".














# End troll commands
# Start DB commads






















# End Db commads





# Start Credit commands












# Function to get user purchases


# Function to add a purchase


# Dictionary of store items with item names as keys and prices as values
store_items = {
    "Flashlight": 7500,
    "Antenna": 7500,
    "Communicator": 7500,
    "Heavy Attachments": 7500,
    "Rangefinder Down": 7500,
    "Helmet Tubes": 7500,
    "Binoculars": 10000,
    "Binoculars Up": 10000,
    "Flight Computer": 15000,
    "Clone Gunner": 20000,
    "Hood": 20000,
    "ARF": 30000,
    "Snowtrooper/Flametrooper": 30000,
    "Custom Visor": 30000,
    "Render": 30000,
    "BARC": 35000,
    "Phase 1": 35000,
    "2003 Helmets": 40000,
    "Desert": 45000,
    "Halfbody": 50000,
    # Add other items here
}






# Command to show purchased items of a user




# Function to remove a purchase


# Command to handle refunding items


















start_time = datetime.now()










from discord.ext import commands

# List of army qualifications to check for, excluding "Clone Trooper Veteran" and "Veteran Trooper"
army_qualifications = [
    "Scout Trooper", "Aerial Trooper", "Engineer", "Ace Pilot", "ARF Trooper",
    "Interceptor Pilot", "Bomber Pilot", "Strike Cadre", "Juggernaut Cadre",
    "Shadow Cadre", "ARC Trooper", "Republic Commando", "Medic Cadre", "Shadow Pilot", "Sapper", "Sky Trooper",
    "HERO Pilot - First Class", "HERO Pilot - Second Class", "Galactic Marine"
]

# Advanced Weaponry Qualifications
advanced_weaponry_qualifications = [
    "Frontliner", "Submachine Gunner", "Rifleman", "CQC Trooper", "Suppressor",
    "Grenadier", "Heavy Rifleman", "Hunter", "Aggressor", "Slug Shooter",
    "Sniper", "Sharpshooter", "Operative", "Urban Warrior", "Gunslinger"
]

# Platform roles
platform_roles = {
    "Personal Computer": "PC",
    "Xbox": "Xbox",
    "Playstation": "PS"
}

# Main platform roles
main_platform_roles = {
    "Green Company": "PC",
    "Krayt Company": "PS",
    "Titan Company": "Xbox"
}


# Function to send long messages in chunks


# Define the bot command



























bot.run(get_bot_token())

