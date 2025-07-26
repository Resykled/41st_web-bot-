import os
import re
import discord
from discord.ext import commands
from discord.ext import tasks
import schedule
import time
import threading
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import numpy as np
import io
from discord import File
date_str = datetime.now(timezone.utc).isoformat()

from dotenv import load_dotenv

# Import the database methods
import db

# Load environment variables from .env
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Initialize DB (creates tables if they don't exist)
db.initialize_database()

# Create the bot client
intents = discord.Intents.default()
intents.message_content = True  # Required if you want to read message content
intents.members = True           # Required if you want to resolve member objects from user IDs
bot = commands.Bot(command_prefix='!', intents=intents)

# ----------------------------
#   PERIODIC SCHEDULING LOGIC
# ----------------------------

def run_scheduler():
    """Runs schedule in a separate thread so it doesn't block the bot."""
    while True:
        schedule.run_pending()
        time.sleep(1)

def two_week_reset():
    """Function triggered by the schedule to finalize the attendance cycle."""
    db.finalize_two_week_cycle()
    print("Attendance has been reset and transferred to all-time stats.")

# Schedule the reset. For demonstration, daily at midnight:
schedule.every().day.at("00:00").do(two_week_reset)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# ----------------------------
#   DISCORD BOT EVENTS
# ----------------------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message):
    """
    Listen for messages in #raid-logs channel, parse them, store to DB.
    Now reacts with ✅ on success, ❌ on format error.
    """
    if message.author == bot.user:
        return


    if message.channel.name == 'raid-logs':
        content = message.content
        lines = content.splitlines()

        host_pattern = r"host:\s*(.*)"
        platform_pattern = r"platform:\s*(.*)"
        raid_type_pattern = r"raid type:\s*(.*)"
        game_pattern = r"game:\s*(.*)"
        attendees_marker = "attendees:"

        host_info = None
        platform_info = None
        raid_type_info = None
        game_info = None

        attendees_lines = []
        is_attendee_section = False

        for line in lines:
            line_stripped = line.strip().lower()

            if line_stripped.startswith("host:"):
                match = re.match(host_pattern, line_stripped, re.IGNORECASE)
                if match:
                    host_info = match.group(1).strip()
                else:
                    print(f"Error with {host_pattern}")

            elif line_stripped.startswith("platform:"):
                match = re.match(platform_pattern, line_stripped, re.IGNORECASE)
                if match:
                    platform_info = match.group(1).strip()
                else:
                    print(f"Error with {platform_pattern}")

            elif line_stripped.startswith("raid type:"):
                match = re.match(raid_type_pattern, line_stripped, re.IGNORECASE)
                if match:
                    raid_type_info = match.group(1).strip()
                else:
                    print(f"Error with {raid_type_pattern}")

            elif line_stripped.startswith("game:"):
                match = re.match(game_pattern, line_stripped, re.IGNORECASE)
                if match:
                    game_info = match.group(1).strip().title()  # Normalize to title case
                else:
                    print(f"Error with {game_pattern}")

            elif line_stripped.startswith(attendees_marker):
                is_attendee_section = True
                continue

            elif is_attendee_section:
                if line_stripped == "":
                    break
                attendees_lines.append(line_stripped)

        # Verify required fields
        if not (host_info and platform_info and raid_type_info and game_info and attendees_lines):
            await message.author.send(f"There was an error in your raid log. Please double check that all spellings, colons, and fields are there.\nGiven fields:\n```{lines}```")
            print("Raid log format invalid or incomplete.")
            await message.add_reaction("❌")
        else:
            (host_id, host_name, host_points) = extract_mention_or_name(host_info)
            date_str = datetime.now(timezone.utc).isoformat()

            # Create raid record
            raid_id = db.record_raid(
                host_id=host_id,
                host_username=host_name,
                raid_type=raid_type_info,
                platform=platform_info,
                game=game_info,
                date_str=date_str
            )

            # Record host attendance and hosting points
            db.record_host_points(host_id, 1)
            db.record_attendance(
                user_id=host_id,
                username=host_name,
                raid_id=raid_id,
                attendance_points=host_points,
                date_str=date_str
            )

            # Parse other attendees
            total_attendance = host_points  # Include host attendance
            for attendee_line in attendees_lines:
                (attendee_id, attendee_name, points) = extract_mention_or_name(attendee_line)
                db.record_attendance(
                    user_id=attendee_id,
                    username=attendee_name,
                    raid_id=raid_id,
                    attendance_points=points,
                    date_str=date_str
                )
                total_attendance += points

            db.update_raid_stats(raid_id, len(attendees_lines) + 1, total_attendance)  # Include host in total attendees

            print(f"Raid logged successfully (RaidID: {raid_id}).")
            #await message.add_reaction("✅")

    await bot.process_commands(message)



def extract_mention_or_name(line_text):
    """
    Utility function to parse mentions or usernames with multipliers.
    Returns a tuple (user_id, username, points).
    """
    mention_match = re.search(r"<@!?(\d+)>", line_text)
    if mention_match:
        user_id = mention_match.group(1)
        multiplier_match = re.search(r"x(\d+)$", line_text)
        points = int(multiplier_match.group(1)) if multiplier_match else 1
        username = user_id
    else:
        multiplier_match = re.search(r"x(\d+)$", line_text)
        points = int(multiplier_match.group(1)) if multiplier_match else 1
        username = re.sub(r"x(\d+)$", "", line_text).strip()
        user_id = username
    return (user_id, username, points)

@bot.command(name="raid_data")
@commands.has_any_role('Commander', 'Technical Commander', 'Captain', 'Major', 'High Command')
async def raid_data(ctx):
    """
    Provides detailed raid statistics with main and sub-bars for raid types.
    Usage: !raid_data
    """
    # Fetch data from the database
    raid_data, top_raid_type = db.get_raid_statistics()

    if not raid_data:
        await ctx.send("No raid data available.")
        return

    # Dynamically process games and raid types
    games = list(raid_data.keys())
    total_attendance = [raid_data[game]["total"] for game in games]

    raid_types = set()
    for raids in raid_data.values():
        raid_types.update(raids.keys())
    raid_types.discard("total")
    raid_types = list(raid_types)

    raid_type_data = {
        rtype: [raid_data[game].get(rtype, 0) for game in games] for rtype in raid_types
    }

    x = np.arange(len(games))  # Position of groups
    bar_width = 0.9 / (len(raid_types) + 1)  # Adjust bar width to fit all bars tightly

    plt.figure(figsize=(14, 8))

    # Plot each raid type with stack
    bottom_stack = [0] * len(games)  # Initialize bottom stack
    for rtype, values in raid_type_data.items():
        plt.bar(
            x, values,
            width=bar_width,
            label=rtype,
            bottom=bottom_stack,
            alpha=0.85
        )
        bottom_stack = [sum(x) for x in zip(bottom_stack, values)]

    # Add grid for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Add labels, title, and legend
    plt.title("Attendance by Game and Raid Type", fontsize=18, fontweight='bold')
    plt.xlabel("Games", fontsize=14)
    plt.ylabel("Attendance Points", fontsize=14)
    plt.xticks(x, games, rotation=15, fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(title="Raid Types", fontsize=10, loc='upper left', bbox_to_anchor=(1, 1))

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', bbox_inches="tight")
    buf.seek(0)
    plt.close()

    # Send the plot to the user
    user = ctx.author
    await user.send("Here is a visualization of the updated raid data:", file=File(buf, filename="raid_data.png"))

    # Split the summary into chunks if too long
    summary_lines = [
        f"{game}: Total - {raid_data[game]['total']} points, " +
        ", ".join(f"{rtype} - {raid_data[game].get(rtype, 0)} points" for rtype in raid_types)
        for game in games
    ]
    summary_chunks = [summary_lines[i:i + 10] for i in range(0, len(summary_lines), 10)]

    for chunk in summary_chunks:
        await ctx.send(f"**Raid Data Summary:**\n\n" + "\n".join(chunk))


@bot.command(name="reset")
@commands.has_any_role('Commander', 'Technical Commander', 'Captain', 'Major', 'High Command')
@commands.has_permissions(administrator=True)
async def reset_db_command(ctx):
        """
        A testing command to clear the entire database.
        Only accessible to admins.
        Usage: !reset
        """
        db.reset_database()
        await ctx.send("**All data cleared.** Database has been reset.")



# ----------------------------
#   RUN THE BOT
# ----------------------------
def get_bot_token():
    with open('Bot-Token.txt', 'r') as file:
        return file.read().strip()

bot.run(get_bot_token())
