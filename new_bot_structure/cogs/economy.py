import discord
from discord.ext import commands
import asyncio
import random
import time
import sqlite3
from datetime import datetime, timedelta
from utils import *
from database import *

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def role_credits(self):
        return self.bot.role_credits

    @property
    def non_stacking_roles(self):
        return self.bot.non_stacking_roles

    @property
    def non_stacking_role_credits(self):
        return self.bot.non_stacking_role_credits

    @commands.command()
    @commands.has_any_role('Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander')
    @commands.check(is_registered)
    async def add(self, ctx, member: discord.Member, amount: int, *, comment: str = None):
        try:
            user_id = member.id
            credits_data = get_user_credits(user_id, member.roles, self.role_credits, self.non_stacking_roles)
            current_credits = credits_data[0] if credits_data else 0
            new_credits = current_credits + amount
    
            update_user_credits(user_id, new_credits)
    
            # Log activity in database-activity channel
            activity_channel = discord.utils.get(ctx.guild.text_channels, name="database-activity")
            if activity_channel:
                log_message = f"Added {amount} credits to {member.mention}. New balance: {new_credits} credits."
                if comment:
                    log_message += f" Comment: {comment}"
                await activity_channel.send(log_message)
    
            await ctx.send(f"Added {amount} credits to {member.mention}. New balance: {new_credits} credits.")
            print(f'Added {amount} credits to {member.mention} (ID: {member.id}). New balance: {new_credits}')
        except Exception as e:
            await ctx.send(f"An error occurred while adding credits: {e}")
            print(f"An error occurred while adding credits: {e}")

    @commands.command()
    @commands.has_any_role('Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander')
    @commands.check(is_registered)
    async def remove(self, ctx, member: discord.Member, amount: int, *, comment: str = None):
        try:
            user_id = member.id
            credits_data = get_user_credits(user_id, member.roles, self.role_credits, self.non_stacking_roles)
            current_credits = credits_data[0] if credits_data else 0
            new_credits = current_credits - amount
            removed_credits = amount  # Die Anzahl der entfernten Credits
    
            update_user_credits(user_id, new_credits, removed_credits)
    
            # Log activity in database-activity channel
            activity_channel = discord.utils.get(ctx.guild.text_channels, name="database-activity")
            if activity_channel:
                log_message = f"Removed {amount} credits from {member.mention}. New balance: {new_credits} credits."
                if comment:
                    log_message += f" Comment: {comment}"
                await activity_channel.send(log_message)
    
            await ctx.send(f"Removed {amount} credits from {member.mention}. New balance: {new_credits} credits.")
            print(f'Removed {amount} credits from {member.mention} (ID: {member.id}). New balance: {new_credits}')
        except Exception as e:
            await ctx.send(f"An error occurred while removing credits: {e}")
            print(f"An error occurred while removing credits: {e}")

    @commands.command()
    @commands.has_any_role('Economy Lead', 'Commander', 'Technical Commander')
    @commands.check(is_registered)
    async def setUserCredits(self, ctx, member: discord.Member, credits: int, *, comment: str = None):
        try:
            user_id = member.id
            executor_name = ctx.author.display_name
    
            # Connect to the database
            connection = sqlite3.connect('credits.db')
            cursor = connection.cursor()
    
            # Check if user already exists in the database
            cursor.execute('SELECT user_id FROM user_credits WHERE user_id = ?', (user_id,))
            data = cursor.fetchone()
    
            if data:
                # User exists, update their credits
                cursor.execute('UPDATE user_credits SET current_credits = ?, max_credits = ? WHERE user_id = ?',
                               (credits, credits, user_id))
                print(f'Updated credits for user {user_id}: {credits}')
            else:
                # User does not exist, add them with the provided credits
                cursor.execute(
                    'INSERT INTO user_credits (user_id, current_credits, max_credits, removed_credits) VALUES (?, ?, ?, ?)',
                    (user_id, credits, credits, 0))
                print(f'Added new user {user_id} with credits: {credits}')
    
            # Commit the transaction and close the connection
            connection.commit()
            connection.close()
    
            # Log the transaction
    
            await ctx.send(f"Credits for {member.display_name} have been set to {credits}.")
            print(f"Credits for {member.display_name} ({user_id}) have been set to {credits}.")
        except Exception as e:
            await ctx.send(f"An error occurred while setting credits: {e}")
            print(f"An error occurred while setting credits: {e}")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def credits(self, ctx):
        user_id = ctx.author.id
        member = ctx.author
    
        # Ensure user_roles contains unique role objects
        user_roles = list(set(member.roles))
    
        # Retrieve credits directly from the database
        credits = get_user_credits(user_id, user_roles, self.role_credits, self.non_stacking_roles)
        if credits:
            description = f'You have {credits[0]} credits.'
        else:
            description = 'You do not have any credits.'
    
        print(f'Credits for user {user_id}: {credits[0] if credits else 0}')
    
        embed = discord.Embed(
            title="Your Credits",
            description=description,
            color=discord.Color.red()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    
        await ctx.send(embed=embed)
        print(f"Message sent to {ctx.channel.name}")

    @commands.command()
    @commands.has_any_role('Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander')
    @commands.check(is_registered)
    async def check_credits(self, ctx, member: discord.Member):
        try:
            user_id = member.id
            credits_data = get_user_credits(user_id, member.roles, self.role_credits, self.non_stacking_roles)
            current_credits = credits_data[0] if credits_data else 0
            max_credits = credits_data[1] if len(credits_data) > 1 else 0
            removed_credits = credits_data[2] if len(credits_data) > 2 else 0
    
            embed = discord.Embed(
                title="User Credit Information",
                color=discord.Color.red()
            )
            embed.add_field(name="ID", value=f"{user_id}", inline=False)
            embed.add_field(name="Nickname", value=f"{member.display_name}", inline=False)
            embed.add_field(name="Current Credits", value=f"{current_credits}", inline=False)
            embed.add_field(name="Max Credits", value=f"{max_credits}", inline=False)
            embed.add_field(name="Removed Credits", value=f"{removed_credits}", inline=False)
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
    
            await ctx.send(embed=embed)
            print(f"Credit info for {user_id} sent in embed.")  # Debug: Embed sent
        except Exception as e:
            await ctx.send(f"An error occurred while fetching credit info: {e}")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def daily(self, ctx):
        user_id = ctx.author.id
        current_time = int(time.time())
        daily_info = get_user_daily_info(user_id)
    
        if daily_info:
            last_claim, streak = daily_info
            # Check if last claim was more than 24 hours ago
            if current_time - last_claim < 86400:
                remaining_time = 86400 - (current_time - last_claim)
                hours, remainder = divmod(remaining_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.send(f"{ctx.author.mention}, you can only claim your daily credits once every 24 hours. "
                               f"Time remaining: {hours} hours, {minutes} minutes, {seconds} seconds.")
                return
        else:
            streak = 0
    
        # Calculate the new streak
        if daily_info and current_time - last_claim < 172800:
            streak += 1
        else:
            streak = 1
    
        # Calculate daily credits based on the streak
        daily_credits = min(49 + streak, 80)
    
        # Update the user's credits
        current_credits, _, _ = get_user_credits(user_id, [], {}, {})
        new_credits = current_credits + daily_credits
        update_user_credits(user_id, new_credits)
    
        # Update daily info in the database
        update_user_daily_info(user_id, current_time, streak)
        save_database()  # Save the database state
    
        await ctx.send(
            f"{ctx.author.mention}, you have claimed {daily_credits} credits! Your current streak is {streak} days. You now have {new_credits} credits.")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def leader(self, ctx):
        user_id = ctx.author.id
        top_streaks = get_top_streaks()
        user_position = get_user_position(user_id)
        user_info = get_user_daily_info(user_id)
    
        embed = discord.Embed(
            title="Leaderboard - Top 5 Daily Streaks",
            color=discord.Color.gold()
        )
    
        if top_streaks:
            for i, (uid, streak) in enumerate(top_streaks, start=1):
                user = await self.bot.fetch_user(uid)
                embed.add_field(name=f"{i}. {user.display_name}", value=f"Streak: {streak} days", inline=False)
    
        if user_info:
            user_streak = user_info[1]
            if user_position > 5:
                embed.add_field(name="Your Position",
                                value=f"{user_position}. {ctx.author.display_name} - Streak: {user_streak} days",
                                inline=False)
    
        await ctx.send(embed=embed)

    @commands.command(name='rewards')
    @commands.check(is_registered)
    async def rewards_command(self, ctx):
        user = ctx.author
        roles = user.roles
        role_names = [role.name for role in roles]
        user_rewards = get_rewards_for_roles(role_names)
        if user_rewards:
            rewards_message = "\n\n".join(f"`{role}`: {', '.join(rewards[role])}" for role in role_names if role in rewards)
        else:
            rewards_message = "You have no rewards based on your current roles."
    
        embed = discord.Embed(title="Your Rank Rewards", description=rewards_message, color=discord.Color.red())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
