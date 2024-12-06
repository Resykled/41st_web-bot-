import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.members = True  # Required to access member information
intents.message_content = True  # Required to read message content
intents.reactions = True  # Required to track reactions

bot = commands.Bot(command_prefix='!', intents=intents)

# Function to load game messages from a JSON file
def load_game_messages():
    if os.path.exists('game_messages.json'):
        with open('game_messages.json', 'r') as f:
            data = json.load(f)
            # Ensure IDs are integers
            for game_name, info in data.items():
                info['channel_id'] = int(info['channel_id'])
                info['message_id'] = int(info['message_id'])
            return data
    else:
        return {}

# Function to save game messages to a JSON file
def save_game_messages():
    with open('game_messages.json', 'w') as f:
        json.dump(game_messages, f)

# Function to build a mapping from message IDs to game names
def build_message_id_to_game():
    return {int(info['message_id']): game_name for game_name, info in game_messages.items()}

# Load existing game messages and build the message ID mapping
game_messages = load_game_messages()
message_id_to_game = build_message_id_to_game()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def add(ctx, *, game_name):
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=game_name)
    if role is None:
        await ctx.send(f"Role '{game_name}' does not exist.")
        return
    emoji = discord.utils.get(guild.emojis, name=game_name)
    if emoji is None:
        await ctx.send(f"Emoji ':{game_name}:' does not exist.")
        return
    # Create the message
    message = await ctx.send(f"React with {emoji} to get the '{game_name}' role!")
    # React to the message with the emoji
    await message.add_reaction(emoji)
    # Store the message ID and channel ID with the game name
    game_messages[game_name] = {'channel_id': ctx.channel.id, 'message_id': message.id}
    save_game_messages()
    message_id_to_game[message.id] = game_name

@bot.command()
async def remove(ctx, *, game_name):
    # Remove the role from all users
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=game_name)
    if role is None:
        await ctx.send(f"Role '{game_name}' does not exist.")
        return
    for member in guild.members:
        if role in member.roles:
            try:
                await member.remove_roles(role)
            except Exception as e:
                print(f"Could not remove role from {member}: {e}")
    # Delete the bot's message related to the game
    message_info = game_messages.get(game_name)
    if message_info:
        channel_id = message_info['channel_id']
        message_id = message_info['message_id']
        channel = bot.get_channel(channel_id)
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
            del game_messages[game_name]
            save_game_messages()
            del message_id_to_game[message_id]
        except Exception as e:
            print(f"Could not delete message: {e}")
    else:
        await ctx.send(f"No message found for game '{game_name}'.")

@bot.event
async def on_reaction_add(reaction, user):
    # Ignore reactions from bots
    if user.bot:
        return
    message_id = reaction.message.id
    game_name = message_id_to_game.get(message_id)
    if game_name:
        # Check if the emoji matches
        guild = reaction.message.guild
        game_emoji = discord.utils.get(guild.emojis, name=game_name)
        if reaction.emoji == game_emoji:
            # Assign role
            role = discord.utils.get(guild.roles, name=game_name)
            member = guild.get_member(user.id)
            if role and member:
                await member.add_roles(role)

@bot.event
async def on_reaction_remove(reaction, user):
    # Ignore reactions from bots
    if user.bot:
        return
    message_id = reaction.message.id
    game_name = message_id_to_game.get(message_id)
    if game_name:
        # Check if the emoji matches
        guild = reaction.message.guild
        game_emoji = discord.utils.get(guild.emojis, name=game_name)
        if reaction.emoji == game_emoji:
            # Remove role
            role = discord.utils.get(guild.roles, name=game_name)
            member = guild.get_member(user.id)
            if role and member:
                await member.remove_roles(role)

def get_bot_token():
    with open('Bot-Token.txt', 'r') as file:
        return file.read().strip()

bot.run(get_bot_token())


