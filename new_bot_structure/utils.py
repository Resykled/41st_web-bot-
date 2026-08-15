import discord
from discord.ext import commands
from discord.ext.commands import CommandInvokeError
from database import *

# Channels where the bot commands are allowed
ALLOWED_CHANNEL_NAMES = ['bot-test', 'bot-commands']
REPORT_CHANNEL_NAME = 'bug-reports'

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

async def is_registered(ctx):
    user_id = ctx.author.id
    if not has_registered(user_id) and ctx.command.name != 'register':
        await ctx.send(f"{ctx.author.mention}, you must use `!register` to register before using other commands.")
        raise CommandInvokeError("User not registered.")
    return True

def get_rewards_for_roles(role_names):
    user_rewards = set()
    for role in role_names:
        if role in rewards:
            user_rewards.update(rewards[role])
    return list(user_rewards)

def get_bot_token():
    with open('bot_token.txt', 'r') as file:
        return file.read().strip()

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

async def has_role_elsewhere(member, role_name):
    for guild in bot.guilds:
        if guild != member.guild:  # Prüfen Sie andere Server
            guild_member = guild.get_member(member.id)
            if guild_member and any(role.name == role_name for role in guild_member.roles):
                return True
    return False

def read_medals(file_path):
    medals = {}
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().rsplit(' ', 1)
            if len(parts) == 2:
                medal_name, credit_amount = parts
                try:
                    medals[medal_name] = int(credit_amount)
                except ValueError:
                    print(f"Zeile übersprungen aufgrund ungültigen Formats: {line.strip()}")
    return medals

def is_allowed_channel():
    async def predicate(ctx):
        ALLOWED_CHANNEL_NAMES = ['bot-commands', 'bot-test', 'econ-chat']  # List of allowed channels
        if ctx.channel.name not in ALLOWED_CHANNEL_NAMES:
            await ctx.send(f"This command can only be used in the #{' or #'.join(ALLOWED_CHANNEL_NAMES)} channels.")
            return False
        return True

    return commands.check(predicate)

def is_Technical_Commander():
    async def predicate(ctx):
        bot_dev_role = discord.utils.get(ctx.guild.roles, name="Technical Commander")
        if bot_dev_role in ctx.author.roles:
            return True
        await ctx.send("You do not have permission to use this command.")
        return False

    return commands.check(predicate)



async def send_long_message(ctx, message):
    if len(message) <= 2000:
        await ctx.send(message)
    else:
        # Split the message into chunks of 2000 characters
        for i in range(0, len(message), 2000):
            await ctx.send(message[i:i + 2000])

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
    "Halfbody": 50000
}
