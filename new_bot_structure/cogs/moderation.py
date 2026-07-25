import discord
from discord.ext import commands
import asyncio
import random
from utils import *
from database import *

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx):
        user_id = ctx.author.id
    
        # �berpr�fen, ob der Nutzer bereits registriert ist
        if has_registered(user_id):
            await ctx.send(f"{ctx.author.mention}, you have already used the `!register` command.")
            return
    
        # Definiere Server-IDs, aus denen die Rollen geholt werden sollen
        server_ids = [850840453800919100, 911409562970628167, 1138926753931346090]
    
        # Alle Rollen aus den angegebenen Servern abrufen
        roles_from_servers = get_user_roles_from_servers(user_id, server_ids + [ctx.guild.id])
    
        # Berechnung der Credits basierend auf den Rollen
        credits = 0
        added_non_stacking_roles = set()
        unique_roles = set(roles_from_servers)  # Set zur Sicherstellung von eindeutigen Rollen
    
        for role_name in unique_roles:
            if role_name in role_credits:
                credits += role_credits[role_name]
            if role_name in non_stacking_role_credits and role_name not in added_non_stacking_roles:
                credits += non_stacking_role_credits[role_name]
                added_non_stacking_roles.add(role_name)
    
        # Benutzer-Credits in der Datenbank aktualisieren
        update_user_credits(user_id, credits)
    
        # Nutzer als registriert markieren
        mark_as_registered(user_id)
    
        # R�ckmeldung an den Benutzer
        await ctx.send(f"{ctx.author.mention}, you have been successfully registered with **{credits} credits**.")

    @commands.command()
    @is_Technical_Commander()  # Ensure only admins can use this command
    async def registerRemove(self, ctx, member: discord.Member):
        user_id = member.id
    
        # Remove the registered status
        remove_registered_status(user_id)
    
        await ctx.send(f"{member.mention}'s register status has been reset. They can use the !register command again.")

    @commands.command()
    @is_Technical_Commander()  # Ensure only authorized users can run this command
    async def registerEveryone(self, ctx):
        clone_trooper_role = discord.utils.get(ctx.guild.roles, name="#ddaa00")
        # clone_trooper_role = discord.utils.get(ctx.guild.roles, name="Clone Trooper")
        registered_count = 0
        # Republic Commmando
        # Define the server IDs to fetch roles from
        server_ids = [850840453800919100, 911409562970628167, 1138926753931346090]
    
        for guild in bot.guilds:
            for member in guild.members:
                user_id = member.id
    
                # Skip bot accounts
                if member.bot:
                    continue
    
                # Check if the member has the "Clone Trooper" role
                if clone_trooper_role not in member.roles:
                    continue
    
                # Get roles from all specified servers
                roles_from_servers = get_user_roles_from_servers(user_id, server_ids + [guild.id])
    
                # Calculate credits based on unique roles
                credits = 0
                added_non_stacking_roles = set()
                unique_roles = set(roles_from_servers)  # Use a set to ensure unique roles
    
                for role_name in unique_roles:
                    if role_name in role_credits:
                        credits += role_credits[role_name]
                    if role_name in non_stacking_role_credits and role_name not in added_non_stacking_roles:
                        credits += non_stacking_role_credits[role_name]
                        added_non_stacking_roles.add(role_name)
    
                # Update credits in the database
                update_user_credits(user_id, credits)
    
                # Mark the user as registered
                if not has_registered(user_id):
                    mark_as_registered(user_id)
                    registered_count += 1
    
                # Notify about the update (optional)
                await ctx.send(f"{member.mention} has been registered with {credits} credits.")
    
        await ctx.send(
            f"All members with the 'Clone Trooper' role have been registered. Total registered: {registered_count}")

    @commands.command()  # register help command to remove every user with a certain role
    @is_Technical_Commander()  # Ensure only authorized users can run this command
    async def removeNonCTs(self, ctx):
        clone_trooper_role_name = "ARC Trooper"
        removed_count = 0
        # clone_trooper_role_name = "Clone Trooper"
        for guild in bot.guilds:
            for member in guild.members:
                user_id = member.id
    
                # Check if the member has the "Clone Trooper" role
                if any(role.name == clone_trooper_role_name for role in member.roles):
                    continue
    
                # If the member does not have the "Clone Trooper" role, remove them from the database
                remove_user_from_db(user_id)
                removed_count += 1
                print(f"Removed user {user_id} from the database.")
    
        await ctx.send(f"Removed {removed_count} users who do not have the 'Clone Trooper' role.")

    @commands.command()  # register help command to remove every user with a certain role
    @is_Technical_Commander()  # Ensure only authorized users can run this command
    async def removeARCTroopers(self, ctx):
        arc_trooper_role_name = "ARC Trooper"
        removed_count = 0
    
        for guild in bot.guilds:
            for member in guild.members:
                user_id = member.id
    
                # Check if the member has the "ARC Trooper" role
                if any(role.name == arc_trooper_role_name for role in member.roles):
                    # Remove the user from the database
                    remove_user_from_db(user_id)
                    removed_count += 1
                    print(f"Removed user {user_id} from the database.")
    
        await ctx.send(f"Removed {removed_count} users who have the '{arc_trooper_role_name}' role.")

    @commands.command()
    @is_Technical_Commander()
    @is_allowed_channel()
    async def resetStats(self, ctx, user: discord.Member):
        try:
            reset_user_stats(user.id)
            credits_dict[user.id] = 0
            await ctx.send(f"All statistics for {user.mention} have been reset.")
        except Exception as e:
            await ctx.send(f"An error occurred while resetting statistics for {user.mention}: {e}")

    @commands.command()
    async def sleep(self, ctx, *, duration: str = None):
        """
        Timeout the command invoker (the user who calls this command) for a specified duration.
        Usage: !sleep 1h 30min (for 1 hour and 30 minutes) or !sleep 7 (for 7 hours).
               If no duration is specified, the bot will provide usage instructions.
        """
        from datetime import timedelta
        import re
    
        # If no duration is provided, show usage instructions
        if not duration:
            await ctx.send(
                "Usage: `!sleep <duration>`\n"
                "Examples:\n"
                "- !sleep 7h` to sleep for 7 hours.\n"
                "- `!sleep 1h 30min` to sleep for 1 hour and 30 minutes.\n"
                "Note: The maximum duration is 24 hours."
            )
            return
    
        # Support extended formats like '1h 30min'
        duration_match = re.match(r"(?:(\d+)h)?\s*(?:(\d+)min)?", duration)
        if not duration_match:
            await ctx.send(
                "Invalid duration format! Use a number (e.g., `!sleep 7h`) or specify time like `!sleep 1h 30min`."
            )
            return
    
        # Parse hours and minutes
        hours = int(duration_match.group(1)) if duration_match.group(1) else 0
        minutes = int(duration_match.group(2)) if duration_match.group(2) else 0
    
        # Ensure at least 1 minute
        if hours == 0 and minutes == 0:
            await ctx.send("Duration must be at least 1 minute.")
            return
    
        timeout_duration = timedelta(hours=hours, minutes=minutes)
    
        # Ensure timeout duration does not exceed 24 hours
        max_duration = timedelta(hours=24)
        if timeout_duration > max_duration:
            await ctx.send("The maximum sleep duration is 24 hours. Please provide a shorter duration.")
            return
    
        member = ctx.author  # The user who invoked the command
    
        try:
            # Apply the timeout
            await member.timeout(timeout_duration, reason="Encouraging sleep!")
            await ctx.send(
                f"{member.mention}, you've been put to sleep for {hours} hours and {minutes} minutes. Rest well!"
            )
        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout you.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to apply sleep timeout: {e}")

    @commands.command()
    @commands.has_any_role('Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander', 'Sergeant Major', '2nd Lieutenant', 'Lieutenant', 'Captain', 'Major', 'High Command')
    
    async def mute(self, ctx, member: discord.Member = None, *, duration: str = None):
    
    
    
        # Check if user and duration are provided
        if member is None or duration is None:
            await ctx.send(
                "Usage: !mute @user <duration>\n"
                "Examples:\n"
                "- !mute @user 5d 10h (for 5 days and 10 hours)\n"
                "- !mute @user 5h (for 5 hours)\n"
                "- !mute @user 1d (for 1 day)"
            )
            return
    
    
        duration_match = re.match(r"(?:(\d+)d)?\s*(?:(\d+)h)?", duration)
        if not duration_match:
            await ctx.send(
                "Invalid duration format! Please use 'd' for days and 'h' for hours.\n"
                "Examples:\n"
                "- !mute @user 5d 10h\n"
                "- !mute @user 5h\n"
                "- !mute @user 1d"
            )
            return
    
        # Extract days and hours from the match
        days = int(duration_match.group(1)) if duration_match.group(1) else 0
        hours = int(duration_match.group(2)) if duration_match.group(2) else 0
    
        # Ensure at least one of days or hours is provided
        if days == 0 and hours == 0:
            await ctx.send(
                "Duration must include at least one day or hour component.\n"
                "Examples:\n"
                "- !mute @user 5h\n"
                "- !mute @user 1d\n"
                "- !mute @user 1d 5h"
            )
            return
    
        # Convert the duration into a timedelta
        timeout_duration = timedelta(days=days, hours=hours)
    
        # Attempt to apply the timeout
        try:
            await member.timeout(timeout_duration, reason="Muted via command!")
            # Confirm the action
            await ctx.send(
                f"{member.mention} has been muted for {days} days and {hours} hours."
            )
        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to apply timeout: {e}")

    @commands.command()
    @commands.has_any_role('Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander', 'Sergeant Major', '2nd Lieutenant', 'Lieutenant', 'Captain', 'Major', 'High Command')
    
    async def unmute(self, ctx, member: discord.Member = None):
        """
        Remove the timeout (unmute) from the specified user.
        Usage: !unmute @user
        """
        if member is None:
            await ctx.send("Please mention a user to unmute. Example: !unmute @user")
            return
    
        try:
            # Setting timeout to None removes the current timeout
            await member.timeout(None)
            await ctx.send(f"{member.mention} has been unmuted.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to unmute the user: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
