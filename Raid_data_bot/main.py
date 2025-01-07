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

        host_pattern = r"Host:\s*(.*)"
        platform_pattern = r"Platform:\s*(.*)"
        raid_type_pattern = r"Raid Type:\s*(.*)"
        game_pattern = r"Game:\s*(.*)"
        attendees_marker = "Attendees:"

        host_info = None
        platform_info = None
        raid_type_info = None
        game_info = None

        attendees_lines = []
        is_attendee_section = False

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith("Host:"):
                match = re.match(host_pattern, line_stripped, re.IGNORECASE)
                if match:
                    host_info = match.group(1).strip()

            elif line_stripped.startswith("Platform:"):
                match = re.match(platform_pattern, line_stripped, re.IGNORECASE)
                if match:
                    platform_info = match.group(1).strip()

            elif line_stripped.startswith("Raid Type:"):
                match = re.match(raid_type_pattern, line_stripped, re.IGNORECASE)
                if match:
                    raid_type_info = match.group(1).strip()

            elif line_stripped.startswith("Game:"):
                match = re.match(game_pattern, line_stripped, re.IGNORECASE)
                if match:
                    game_info = match.group(1).strip().title()  # Normalize to title case

            elif line_stripped.startswith(attendees_marker):
                is_attendee_section = True
                continue

            elif is_attendee_section:
                if line_stripped == "":
                    break
                attendees_lines.append(line_stripped)

        # Verify required fields
        if not (host_info and platform_info and raid_type_info and game_info and attendees_lines):
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
            await message.add_reaction("✅")

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

# ----------------------------
#   BOT COMMANDS
# ----------------------------

@bot.command(name="raid_info")
async def raid_info(ctx):
    """
    Provides statistics about raids.
    Usage: !raid_info
    """
    try:
        # Fetch data from the database
        top_games, top_raid_type = db.get_raid_statistics()

        # Check if top_games data exists
        if not top_games:
            await ctx.send("No raid data available.")
            return

        # Format top games text
        top_games_text = "\n".join(
            [f"{i+1}. {game[0]} - {game[1]} attendance points" for i, game in enumerate(top_games)]
        )

        # Handle the case where top_raid_type might not exist
        top_raid_type_text = top_raid_type[0] if top_raid_type else "No data"

        # Build the response
        response = (
            f"**Raid Statistics:**\n\n"
            f"Top 5 Games by Attendance:\n{top_games_text}\n\n"
            f"Most Used Raid Type: {top_raid_type_text}"
        )

        # Send the response
        await ctx.send(response)

    except Exception as e:
        # Catch and log errors, and notify the user
        print(f"Error in !raid_info: {e}")
        await ctx.send("An error occurred while fetching raid statistics. Please try again later.")


@bot.command(name="attendance")
async def attendance(ctx):
    """
    Shows the calling user's attendance totals.
    Usage: !attendance
    """
    user_id = str(ctx.author.id)
    # Fetch attendance data from the updated database
    user_data = db.get_user_attendance(user_id)
    if not user_data:
        await ctx.send(f"**{ctx.author.display_name}'s Attendance**\nNo data found.")
        return

    current_att, current_host, all_time_att, all_time_host = user_data
    await ctx.send(
        f"**{ctx.author.display_name}'s Attendance**\n"
        f"Current Attendance: {current_att}\n"
        f"Current Hosting: {current_host}\n"
        f"All-Time Attendance: {all_time_att}\n"
        f"All-Time Hosting: {all_time_host}"
    )

@bot.command(name="raid_data")
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

    raid_type_data = {rtype: [raid_data[game].get(rtype, 0) for game in games] for rtype in raid_types}

    # Create the bar chart
    x = np.arange(len(games))  # Position of groups
    num_bars = len(raid_types) + 1  # Total bars per group including "Total Attendance"
    bar_width = 0.9 / num_bars  # Adjust bar width to reduce white spaces

    plt.figure(figsize=(12, 8))

    # Plot each category
    for i, (rtype, values) in enumerate(raid_type_data.items()):
        plt.bar(x + (i - num_bars / 2) * bar_width + bar_width / 2, values, width=bar_width, label=rtype, alpha=0.7)

    # Plot total attendance as the last bar
    plt.bar(x + (num_bars - 1 - num_bars / 2) * bar_width + bar_width / 2, total_attendance, width=bar_width, color='blue', label='Total Attendance')

    # Add labels, title, and legend
    plt.title("Attendance by Game and Raid Type", fontsize=16)
    plt.xlabel("Games", fontsize=12)
    plt.ylabel("Attendance Points", fontsize=12)
    plt.xticks(x, games, rotation=0)
    plt.legend(title="Raid Types", fontsize=10)

    # Save the plot to a buffer
    buf = io.BytesIO()
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



@bot.command(name="attendance_check")
async def attendance_check(ctx, member: discord.Member = None):
    """
    Checks another user's attendance record.
    Usage: !attendance_check @user
    """
    if not member:
        await ctx.send("Please mention a user to check, e.g. !attendance_check @username.")
        return

    user_id = str(member.id)
    # Fetch attendance data from the updated database
    user_data = db.get_user_attendance(user_id)
    if not user_data:
        await ctx.send(f"**{member.display_name}'s Attendance**\nNo data found.")
        return

    current_att, current_host, all_time_att, all_time_host = user_data
    await ctx.send(
        f"**{member.display_name}'s Attendance**\n"
        f"Current Attendance: {current_att}\n"
        f"Current Hosting: {current_host}\n"
        f"All-Time Attendance: {all_time_att}\n"
        f"All-Time Hosting: {all_time_host}"
    )


@bot.command(name="check_platoon")
async def check_platoon(ctx, platoon_name: str = None):
    """
    Usage: !check_platoon Brumac
    This will look for a Discord Role named "Brumac Platoon" and list attendance
    for all members who have that role.
    """
    if not platoon_name:
        await ctx.send("Please specify a platoon name, e.g. !check_platoon Brumac.")
        return

    # Construct the role name e.g. "Brumac Platoon"
    role_name = f"{platoon_name} Platoon"

    # Find the role in the guild
    platoon_role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not platoon_role:
        await ctx.send(f"No role found named '{role_name}'. "
                       f"Make sure the role exists and uses this exact format.")
        return

    # Gather all members that have this role
    platoon_members = [member for member in ctx.guild.members if platoon_role in member.roles]

    if not platoon_members:
        await ctx.send(f"No members found with the role '{role_name}'.")
        return

    response_lines = [f"**{platoon_name} Platoon Attendance**"]
    for member in platoon_members:
        user_id = str(member.id)
        # Fetch attendance data from the updated database
        user_data = db.get_user_attendance(user_id)
        if user_data:
            current_att, current_host, _, _ = user_data
            mark = "LOW ATTENDANCE" if current_att < 2 else ""
            response_lines.append(
                f"{member.display_name} - Attendance: {current_att}, Hosts: {current_host} {mark}"
            )
        else:
            response_lines.append(f"{member.display_name} - No data found.")

    # Send a nicely formatted list
    await ctx.send("\n".join(response_lines))


@bot.command(name="reset")
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
