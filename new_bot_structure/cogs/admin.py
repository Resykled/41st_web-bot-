import discord
from discord.ext import commands
import asyncio
import random
import time
import sqlite3
import subprocess
from datetime import datetime, timedelta
from utils import *
from database import *

class Admin(commands.Cog):
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

    @property
    def credits_dict(self):
        return self.bot.credits_dict

    @property
    def rewards(self):
        return self.bot.rewards if hasattr(self.bot, 'rewards') else {}

    @commands.command()  # resets DB ONLY FOR WORST CASE
    @is_Technical_Commander()  # Ensure only authorized users can run this command
    async def cleardb(self, ctx):
        try:
            # Connect to the database
            connection = sqlite3.connect('credits.db')
            cursor = connection.cursor()
    
            # List of tables to be cleared
            tables = ['user_credits', 'self.role_credits', 'self.non_stacking_role_credits', 'update_status', 'register_status']
    
            # Clear all tables
            for table in tables:
                cursor.execute(f'DELETE FROM {table}')
    
            # Commit the changes and close the connection
            connection.commit()
            connection.close()
    
            await ctx.send("All data has been cleared from the database.")
            print("All data has been cleared from the database.")
    
        except Exception as e:
            await ctx.send(f"An error occurred while clearing the database: {str(e)}")
            print(f"An error occurred while clearing the database: {str(e)}")

    @commands.command()
    @is_Technical_Commander()
    @is_allowed_channel()
    async def save_db(self, ctx):
        try:
            save_database()
            embed = discord.Embed(
                title="Save Successful",
                description="Database has been saved locally.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
        except FileNotFoundError as e:
            embed = discord.Embed(
                title="File Not Found Error",
                description=f"The database file was not found: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
        except sqlite3.Error as e:
            embed = discord.Embed(
                title="SQLite Error",
                description=f"An SQLite error occurred while saving the database: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
        except Exception as e:
            embed = discord.Embed(
                title="Unexpected Error",
                description=f"An unexpected error occurred while saving the database: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @is_Technical_Commander()
    async def shutdown(self, ctx):
        await ctx.invoke(save_db)
        await ctx.send("Bot is shutting down...")
        await self.bot.close()

    @commands.command()
    @is_Technical_Commander()
    async def kill(self, ctx):
        await ctx.invoke(save_db)
        await ctx.send("Bot is restarting...")
    
        # Restart the bot using the shell script
        os.system("/home/dominik/Downloads/DiscordBOT/start_bot.sh")
        await self.bot.close()

    @commands.command(name='debug')
    @is_Technical_Commander()
    async def debug(self, ctx):
        """
        Tests all commands except !kill, !resetStats, !cleardb, !registerEveryone, !removeNonCts, and !registerRemove.
        """
        test_commands = [
            "!hello",
            "!credits",
            "!whoami",
            "!whoami medals",
            "!whoami purchases",
            "!whoami stats",
            "!report Test problem report",
            "!version",
            "!help",
            "!ggn_store",
            "!store category",
            "!register",
    
            "!add @user 100",
            "!remove @user 50",
            "!setUserCredits @user",
            "!save_db",
            "!id @user",
            "!check_credits @user"
        ]
    
        results = []
    
        await ctx.send("Starting debug process...")
    
        for command in test_commands:
            await ctx.send(f"Testing command: {command}")
            print(f"Debug: Testing command: {command}")  # Debugging message
    
            try:
                # Extract the command and its arguments
                parts = command.split()
                cmd_name = parts[0][1:]  # Remove the '!' prefix
                cmd_args = parts[1:]
    
                # Simulate mentions for commands that require user mentions
                if '@user' in cmd_args:
                    cmd_args = [arg.replace('@user', str(ctx.author.id)) for arg in cmd_args]
    
                # Find the command object
                cmd = self.bot.get_command(cmd_name)
                if cmd:
                    # Invoke the command
                    await ctx.invoke(cmd, *cmd_args)
                    await ctx.send(f"Successfully tested command: {command}")
                    print(f"Debug: Successfully tested command: {command}")  # Debugging message
                    results.append((command, "✅"))
                else:
                    await ctx.send(f"Command not found: {command}")
                    print(f"Debug: Command not found: {command}")  # Debugging message
                    results.append((command, "❌"))
    
            except Exception as e:
                await ctx.send(f"Error testing command {command}: {e}")
                print(f"Debug: Error testing command {command}: {e}")  # Debugging message
                results.append((command, "❌"))
    
        # Generate the result message
        result_message = "\n".join([f"{command}: {result}" for command, result in results])
        await ctx.send(f"Debugging completed.\n\nResults:\n{result_message}")
        print("Debug: Debugging completed.")  # Debugging message

    @commands.command()
    @is_allowed_channel()
    @is_Technical_Commander()
    async def git_push(self, ctx, branch="main"):
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
    
            # Check if there are changes to commit
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if result.stdout:
                # Commit changes if there are any
                subprocess.run(['git', 'commit', '-m', 'Automated backup commit from bot'], check=True)
    
            # Push changes to the specified branch (default: main)
            subprocess.run(['git', 'push', 'origin', branch], check=True)
    
            # Send success message with repository link
            repo_url = "https://github.com/DominikLinkl/41st_web-bot-"
            await ctx.send(
                f"{ctx.author.mention}, changes have been pushed to the Git repository successfully on branch `{branch}`. Repository link: {repo_url}")
        except subprocess.CalledProcessError as e:
            await ctx.send(f"{ctx.author.mention}, there was an error pushing changes to the Git repository: {e}")
    
        except Exception as e:
            await ctx.send(f"{ctx.author.mention}, an unexpected error occurred: {e}")

    @commands.command()
    @commands.check(is_registered)
    async def Test(self, ctx):
        embed = discord.Embed(
            title="Hello!",
            description="Greetings from the bot.",
            color=discord.Color.red()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        print(f"Message sent to {ctx.channel.name}")

    @commands.command(name='test_chat')
    async def debug_channel(self, ctx):
        channel = ctx.channel
        permissions = channel.permissions_for(ctx.guild.me)
    
        reasons = []
    
        # Check if the bot has send message permission
        if not permissions.send_messages:
            reasons.append("Bot lacks 'send_messages' permission.")
    
        # Check if the bot has read messages permission
        if not permissions.read_messages:
            reasons.append("Bot lacks 'read_messages' permission.")
    
        # Check if the bot is allowed to embed links
        if not permissions.embed_links:
            reasons.append("Bot lacks 'embed_links' permission.")
    
        # Check if the bot can attach files
        if not permissions.attach_files:
            reasons.append("Bot lacks 'attach_files' permission.")
    
        # Check if the bot can add reactions
        if not permissions.add_reactions:
            reasons.append("Bot lacks 'add_reactions' permission.")
    
        # Check if the bot is not allowed due to a channel being NSFW
        if channel.is_nsfw():
            reasons.append("Channel is marked as NSFW.")
    
        # If no reasons were found, assume the bot can send messages
        if not reasons:
            reasons.append("Bot should be able to send messages in this channel.")
    
        # Print the reasons to the console
        for reason in reasons:
            print(f"Debug: {reason}")
    
        # Send a response to the user
        await ctx.send("Check the console for debug information.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
