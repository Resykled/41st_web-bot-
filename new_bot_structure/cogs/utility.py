import discord
from discord.ext import commands
import asyncio
import random
import time
import re
from datetime import datetime, timedelta
from utils import *
from database import *

REPORT_CHANNEL_NAME = 'bug-reports'
ALLOWED_CHANNEL_NAMES = ['bot-test', 'bot-commands']

class Utility(commands.Cog):
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

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def hello(self, ctx):
        embed = discord.Embed(
            title="Hello!",
            description="Greetings from the bot.",
            color=discord.Color.red()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        print(f"Message sent to {ctx.channel.name}")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def report(self, ctx, *, problem: str = None):
        if problem is None:
            bug_report_info = (
                "To report a bug, please use the following format:\n"
                "For example: `!report The credits command is not working correctly.`"
            )
            embed_info = discord.Embed(
                title="How to Report Bugs",
                description=bug_report_info,
                color=discord.Color.red()
            )
            await ctx.send(embed=embed_info)
            return
    
        report_channel = discord.utils.get(ctx.guild.text_channels, name=REPORT_CHANNEL_NAME)
        if report_channel:
            try:
                await report_channel.send(f'Report from {ctx.author.mention}: {problem}')
                embed = discord.Embed(
                    title="Report Sent",
                    description=f'Thank you for your report. It has been sent to the #{REPORT_CHANNEL_NAME} channel.',
                    color=discord.Color.red()
                )
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    
                await ctx.send(embed=embed)
    
                # Send message to user explaining the !report_bug command
                bug_report_info = (
                    "Thank you for your report. If you encounter any bugs, please use the `!report_bug` command to report them. "
                    "For example: `!report_bug The credits command is not working correctly.`"
                )
                embed_info = discord.Embed(
                    title="How to Report Bugs",
                    description=bug_report_info,
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed_info)
            except discord.errors.Forbidden:
                embed = discord.Embed(
                    title="Error",
                    description=f'Error: Missing permissions to send a message in the #{REPORT_CHANNEL_NAME} channel.',
                    color=discord.Color.red()
                )
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description=f'Error: The report channel #{REPORT_CHANNEL_NAME} does not exist.',
                color=discord.Color.red()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    
            await ctx.send(embed=embed)

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def version(self, ctx):
        version_info = (
            "Version: `V1.7~ Purchase`\n"
            "Date: `05.06.2024`\n"
            "Last update: `27.07.2024`\n"
            "Programmer: `TCDR Sykles CC-5132`"
        )
        embed = discord.Embed(
            description=version_info,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name='help')
    @is_allowed_channel()
    @commands.check(is_registered)
    async def help_command(self, ctx):
        admin_roles = ['Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander']
        is_admin = any(discord.utils.get(ctx.guild.roles, name=role) in ctx.author.roles for role in admin_roles)
    
        user_commands = (
            f"`List of available commands:`\n\n"
            f"`!hello`: Sends a simple greeting message.\n"
            f"`!credits`: Displays your current credits.\n"
            f"`!whoami`: Sends your information, including join date and credits, via direct message.\n"
            f"`!report <problem>`: Sends a report message to the designated 'bug' channel.\n"
            f"`!version`: Displays the current version of the bot.\n"
            f"`!help`: Lists all available commands and their descriptions.\n"
            f"`!ggn_store`: Displays Geetsly's Gaming Network Store Conversions.\n"
            f"`!store <category>`: Displays store items for a specific credit category.\n"
            f"`!register`: Registers a new user in the database.\n"
            f"`!purchase`: Command to buy items.\n"
            f"`!daily`: Get your daily reward and build a streak, you better don't miss a day.\n"
            f"`!leader`: Shows you your position in the !daily ranking list.\n"
            f"`!rules`: Shows you all the rules the server has .\n"
            f"`!ct_number`: Generates an new CT number (only for SGM and above).\n"
            f"`!helmets`: shows you an list of all attachments you can put on your helmet .\n"
            f"`!ranks`: Get a brief introduction to each rank and its function .\n"
            f"`!sleep`: Time yourself out and get some sleep without noticifactions from the server  .\n"
            f"\n"
        )
    
        admin_commands = (
            f"`Developer Commands:`\n"
            f"\n"
            f"`!addrole <credit_amount> <role_name>`: Adds a role with a specific credit amount.\n"
            f"`!removerole <role_name>`: Removes a role and its associated credits.\n"
            f"`!debug`: Runs a series of tests on all commands to check for errors.\n"
            f"`!add <@user> <amount> <comment, not necessary>`: Adds credits to a user.\n"
            f"`!remove <@user> <amount> <comment, not necessary>`: Sets the credit amount of a user.\n"
            f"`!setUserCredits <@user> <amount>`: Sets the credit amount of a user to the given number.\n"
            f"`!save_db`: Saves all data to the SQL database.\n"
            f"`!resetStats <@user>`: Resets all data for a specific user.\n"
            f"`!id <@user>`: Sends all information about the mentioned user via direct message.\n"
            f"`!registerRemove <@user>`: Resets the register status of a user.\n"
            f"`!registerEveryone`: Registers every user on the server in the database.\n"
            f"`!removeNonCTs`: Removes every user without the clone trooper role from the db.\n"
            f"`!useritems <@user>`: Shows all items a user has.\n"
        )
    
        help_message = user_commands
        if is_admin:
            help_message += admin_commands
    
        embed = discord.Embed(
            description=help_message,
            color=discord.Color.red()
        )
    
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role('Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander')
    @commands.check(is_registered)
    async def id(self, ctx, member: discord.Member):
        try:
            user_id = member.id
            credits_data = get_user_credits(user_id, member.roles, self.role_credits, self.non_stacking_roles)
            current_credits = credits_data[0] if credits_data else 0
            max_credits = credits_data[1] if len(credits_data) > 1 else 0
            removed_credits = credits_data[2] if len(credits_data) > 2 else 0
            joined_at = member.joined_at.strftime("%b %d, %Y")
    
            embed = discord.Embed(
                title="User Information",
                color=discord.Color.red()
            )
            embed.add_field(name="ID", value=f"{user_id}", inline=False)
            embed.add_field(name="Name", value=f"{member.display_name}", inline=False)
            embed.add_field(name="Current Credits", value=f"{current_credits}", inline=False)
            embed.add_field(name="Max Credits", value=f"{max_credits}", inline=False)
            embed.add_field(name="Removed Credits", value=f"{removed_credits}", inline=False)
            embed.add_field(name="Joined At", value=f"{joined_at}", inline=False)
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
    
            await ctx.send(embed=embed)
            print(f"User info for {user_id} sent in embed.")  # Debug: Embed sent
        except Exception as e:
            await ctx.send(f"An error occurred while fetching user info: {e}")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def website(self, ctx):
        await ctx.send("https://geetslys41st.com")   

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def oldest(self, ctx):
        message = "```We know you are the first member Izzy, but you don't get a special medal```"
        await ctx.send(message)
        print("Sent anniversary message.")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def whoami(self, ctx, subcommand: str = None):
        global role
        user = ctx.author
        server_ids = [850840453800919100, 1138926753931346090, 911409562970628167]
        user_roles = get_user_roles_from_servers(user.id, server_ids)
    
        user_roles = [discord.utils.get(ctx.guild.roles, name=role_name) for role_name in user_roles if
                      discord.utils.get(ctx.guild.roles, name=role_name)]
    
        print(f"User roles from servers: {[role.name for role in user_roles if role]}")
    
        non_stacking_roles_list = [
            "Clone Pilot", "Clone Trooper", "Flight Officer", "Lance Corporal", "Corporal", "Flight Captain", "Sergeant",
            "ARC Sergeant", "RC Sergeant", "Staff Sergeant", "Sergeant Major", "Flight Commander", "2nd Lieutenant",
            "Flight Lieutenant" "Lieutenant", "ARC Lieutenant", "RC Lieutenant", "Quartermaster", "Captain", "ARC Captain",
            "RC Captain", "Colonel", "Major", "Technical Commander", "Commander", "Marshal Commander"
        ]
    
        if subcommand == "medals":
            # Define role categories
            army_medals = [
                "Medal of Valor", "41st Service Medal", "Cadet Master", "Mythical Instructor", "Legendary Instructor",
                "Hero of The 41st", "Absolutely Demolished", "Legendary Ranger", "Battle Hardened", "Bane of Clankers",
                "Order of Dedication", "Vaunted Veteran Medal", "Seppie Scourge", "Plot Armor", "Superior Genetics",
                "Flawless Leadership", "Supporting Act", "May the Score be with you", "Deadly and Discrete",
             "Clanker Crusher", "Terror in the Sky", "True Trooper", "Siegebreaker", "Top Gun",
                "41st Representation Medal", "Lone Survivor", "Exemplar",
                "Professional Soldier", "One Man Army", "The Good Batch", "Bred for War", "Outstanding Dedication",
                "Fireteam on Fire", "First Try", "Experience Outranks Everything", "The Best of the 41st ", "The Legend of the 41st", "The Best of the Best",
            ]
    
            level_medals = [
                "Mythical ARF Medal", "Legendary ARF Medal", "Mythical Engineer Medal", "Elite ARF Medal",
                "Legendary Engineer Medal", "Veteran ARF Medal", "Elite Engineer Medal", "Mythical Commando Medal",
                "Mythical ARC Medal", "Mythical Aerial Medal", "Mythical Officer Medal", "Mythical Specialist Medal",
                "Mythical Heavy Medal", "Mythical Assault Medal", "Veteran Engineer Medal", "Legendary Commando Medal",
                "Legendary ARC Medal", "Legendary Aerial Medal", "Legendary Officer Medal", "Legendary Specialist Medal",
                "Legendary Heavy Medal", "Legendary Assault Medal", "Elite Commando Medal", "Elite ARC Medal",
                "Elite Aerial Medal", "Elite Officer Medal", "Elite Specialist Medal", "Elite Heavy Medal",
                "Elite Assault Medal",
                "Veteran Commando Medal", "Veteran ARC Medal", "Veteran Aerial Medal", "Veteran Officer Medal",
                "Veteran Specialist Medal", "Veteran Heavy Medal", "Veteran Assault Medal"
            ]
    
            army_qualifications = [
                "Scout Trooper", "Aerial Trooper", "Engineer", "Ace Pilot", "ARF Trooper", "Interceptor Pilot",
                "Bomber Pilot", "Veteran Trooper", "Strike Cadre", "Juggernaut Cadre", "Shadow Cadre", "ARC Qualification",
                "Republic Commando", "Frontliner", "Submachine Gunner", "Rifleman", "CQC Trooper", "Suppressor",
                "Grenadier", "Heavy Rifleman", "Hunter", "Aggressor", "Sniper", "Slug Shooter", "Sharpshooter",
                "Operative", "Urban Warrior", "Gunslinger", "HERO Pilot - First Class", "HERO Pilot - Second Class",
                "Galactic Marine", "Medic Cadre", "Shadow Pilot", "Sapper", "Sky Trooper"
            ]
    
            navy_qualifications = [
                "Interceptor Qualification", "Bomber Qualification", "Ace Pilot", "HERO - Dogfighter", "HERO - Objective",
                "HERO - Aerial Denial", "HERO - Mobility", "HERO - Support"
            ]
    
            sof_medals = [
                "SOF Service Medal", "Special Forces Veteran", "Special Forces Legend", "Special Forces Myth",
                "Unexpected Assistance", "Devout Protector", "Strength in Unity", "Brotherhood of Steel",
                "Brothers in Arms",
                "Proven Advisor", "Impossible Odds", "41st Superiority", "Double The Effort", "Regime Toppler",
                "Survivalist", "Unbreakable", "Republic Juggernaut", "Death From Above", "Furry Frenzy", "Back to Basics",
                "Operation:SuppressiveShrout", "Seasoned Saboteur", "Support Scuttler", "Masterful Saboteur", "In And Out",
                "Superior Tactics", "Safety's Off", "Tinnie Scrapper", "Commando Culler", "Guerrilla Tactician",
                "Unwavering",
                "Guardian Angel"
            ]
    
            regiment_medals = [
                "Fixer Upper", "Behind Enemy Lines", "Above and Beyond", "Devout Protectors", "Altered Genetics",
                "Dragway Genetics", "Perfect Attendance", "Honor Roll", "All Terrain Terror", "The Team to Beat",
                "Leading to Victory", "To Sacrifice and Serve", "For the Republic", "Dedication is Key", "Squad Oriented",
                "All but Special Forces", "Top Trainer", "Leading the Charge", "Participation Trophy", "A Cut Above",
                "Base Class Champion", "Trials are our Speciality", "Team Player", "Old but Gold", "He's going for Speed",
                "He's Going the Distance", "Basic Equipment Expert", "Instructor on Fire", "Praise the Maker",
                "FEEL THE WRATH OF THE 41ST"
            ]
    
            # Get medals and qualifications from specific servers
            army_server = self.bot.get_guild(850840453800919100)
            army_roles, level_roles, army_qual_roles, navy_qual_roles = [], [], [], []
            if army_server:
                army_member = army_server.get_member(user.id)
                if army_member:
                    army_roles = [role.name for role in army_member.roles if role.name in army_medals]
                    level_roles = [role.name for role in army_member.roles if role.name in level_medals]
                    army_qual_roles = [role.name for role in army_member.roles if role.name in army_qualifications]
                    navy_qual_roles = [role.name for role in army_member.roles if role.name in navy_qualifications]
    
            sof_server = self.bot.get_guild(911409562970628167)
            sof_roles = []
            if sof_server:
                sof_member = sof_server.get_member(user.id)
                if sof_member:
                    sof_roles = [role.name for role in sof_member.roles if role.name in sof_medals]
    
            regiment_server = self.bot.get_guild(1138926753931346090)
            regiment_roles = []
            if regiment_server:
                regiment_member = regiment_server.get_member(user.id)
                if regiment_member:
                    regiment_roles = [role.name for role in regiment_member.roles if role.name in regiment_medals]
    
            # Prepare the embed
            embed = discord.Embed(title="Your Medals", color=discord.Color.red())
    
            if army_roles:
                embed.add_field(name="Army Medals", value="\n".join(army_roles), inline=False)
            if level_roles:
                embed.add_field(name="Level Medals", value="\n".join(level_roles), inline=False)
            if army_qual_roles:
                embed.add_field(name="Army Qualifications", value="\n".join(army_qual_roles), inline=False)
            if navy_qual_roles:
                embed.add_field(name="Navy Qualifications", value="\n".join(navy_qual_roles), inline=False)
            if sof_roles:
                embed.add_field(name="SOF Medals", value="\n".join(sof_roles), inline=False)
            if regiment_roles:
                embed.add_field(name="Regiment Medals", value="\n".join(regiment_roles), inline=False)
    
            await ctx.send(embed=embed)
    
        elif subcommand == "purchases":
            purchases_list = get_user_purchases(user.id)
            if purchases_list:
                purchases_str = "\n".join(purchases_list)
                embed = discord.Embed(
                    title="Your Purchases",
                    description=purchases_str,
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="Your Purchases",
                    description="You have no purchases.",
                    color=discord.Color.green()
                )
            await ctx.send(embed=embed)
    
        elif subcommand == "stats":
            current_credits, max_credits, removed_credits = get_user_credits(user.id, user_roles, self.role_credits,
                                                                             self.non_stacking_roles)
            join_date = user.joined_at.strftime("%Y-%m-%d %H:%M:%S")
            highest_non_stacking_role = max(
                (role for role in user.roles if role.name in non_stacking_roles_list),
                key=lambda r: non_stacking_roles_list.index(r.name),
                default=None
            )
            army_rank = highest_non_stacking_role.name if highest_non_stacking_role else "No rank"
    
            embed = discord.Embed(
                title="Your Stats",
                color=discord.Color.purple()
            )
            embed.add_field(name="Username", value=user.display_name, inline=False)
            embed.add_field(name="Join Date", value=join_date, inline=False)
            embed.add_field(name="Army Rank", value=army_rank, inline=False)
            embed.add_field(name="Max Credits", value=max_credits, inline=False)
            embed.add_field(name="Current Credits", value=current_credits, inline=False)
            embed.add_field(name="Removed Credits", value=removed_credits, inline=False)
    
            await ctx.send(embed=embed)
    
        elif subcommand == "credits":
            current_credits, max_credits, removed_credits = get_user_credits(user.id, user_roles, self.role_credits,
                                                                             self.non_stacking_roles)
            highest_non_stacking_role = max(
                (role for role in user.roles if role.name in non_stacking_roles_list),
                key=lambda r: non_stacking_roles_list.index(r.name),
                default=None
            )
            army_rank = highest_non_stacking_role.name if highest_non_stacking_role else "No rank"
    
            user = ctx.author
            roles = user.roles
            role_names = [role.name for role in roles]
            user_rewards = get_rewards_for_roles(role_names)
            reward_items = {item for rewards_list in rewards.values() for item in rewards_list}
            if user_rewards:
                rewards_message = "\n\n".join(
                    f"{role}: {', '.join(rewards[role])}" for role in role_names if role in rewards)
            else:
                rewards_message = "You have no rewards based on your current roles."
    
            purchases_list = get_user_purchases(user.id)
    
            purchase_roles = [item for item in purchases_list if item in store_items and item not in user_rewards]
            purchase_credits = [str(-store_items[item]) for item in purchase_roles]
            purchases_list_f = "\n".join(f"{role} {credit}" for role, credit in zip(purchase_roles, purchase_credits))
    
            purchase_roles = [item for item in purchases_list if item in store_items and item not in reward_items]
            purchase_credits = [str(-store_items[item]) for item in purchase_roles]
            purchases_list_f = "\n".join(f"{role} {credit}" for role, credit in zip(purchase_roles, purchase_credits))
    
            # Define role categories
            army_medals = [
                ("Medal of Valor", 20000),
            ("41st Service Medal", 3000),
            ("Cadet Master", 9000),
            ("Mythical Instructor", 6000),
            ("Legendary Instructor", 3000),
            ("Hero of The 41st", 6500),
            ("Absolutely Demolished", 2000),
            ("Legendary Ranger", 4000),
            ("Battle Hardened", 2000),
            ("Bane of Clankers", 3500),
            ("Order of Dedication", 2000),
            ("Outstanding Dedication", 6000),
            ("Vaunted Veteran Medal", 4000),
            ("Seppie Scourge", 1500),
            ("Plot Armor", 1500),
            ("Superior Genetics", 1500),
            ("Flawless Leadership", 1500),
            ("Supporting Act", 1000),
            ("May the Score be with you", 1000),
            ("Deadly and Discrete", 1000),
            ("The Best of the Best", 1000),
            ("Clanker Crusher", 1000),
            ("Terror in the Sky", 1000),
            ("True Trooper", 1000),
            ("Siegebreaker", 1000),
            ("Top Gun", 1000),
            ("41st Representation Medal", 1000),
            ("Professional Soldier", 15000),
            ("Experience Outranks Everything", 18500),
            ("The Best of the 41st", 20000 ),
            ("The Legend of the 41st", 25000)
            ]
            level_medals = [
                ("Mythical ARF Medal", 7500),
            ("Legendary ARF Medal", 6000),
            ("Mythical Engineer Medal", 5000),
            ("Elite ARF Medal", 4500),
            ("Legendary Engineer Medal", 4000),
            ("Veteran ARF Medal", 3000),
            ("Elite Engineer Medal", 3000),
            ("Mythical Commando Medal", 2500),
            ("Mythical ARC Medal", 2500),
            ("Mythical Aerial Medal", 2500),
            ("Mythical Officer Medal", 2500),
            ("Mythical Specialist Medal", 2500),
            ("Mythical Heavy Medal", 2500),
            ("Mythical Assault Medal", 2500),
            ("Veteran Engineer Medal", 2000),
            ("Legendary Commando Medal", 2000),
            ("Legendary ARC Medal", 2000),
            ("Legendary Aerial Medal", 2000),
            ("Legendary Officer Medal", 2000),
            ("Legendary Specialist Medal", 2000),
            ("Legendary Heavy Medal", 2000),
            ("Legendary Assault Medal", 2000),
            ("Elite Commando Medal", 1500),
            ("Elite ARC Medal", 1500),
            ("Elite Aerial Medal", 1500),
            ("Elite Officer Medal", 1500),
            ("Elite Specialist Medal", 1500),
            ("Elite Heavy Medal", 1500),
            ("Elite Assault Medal", 1500),
            ("Veteran Commando Medal", 1000),
            ("Veteran ARC Medal", 1000),
            ("Veteran Aerial Medal", 1000),
            ("Veteran Officer Medal", 1000),
            ("Veteran Specialist Medal", 1000),
            ("Veteran Heavy Medal", 1000),
            ("Veteran Assault Medal", 1000),
            ("Lone Survivor", 5000),
            ("Exemplar", 1000),
            ("One Man Army", 1500),
            ("The Good Batch", 4000),
            ("Bred for War", 1500),
            ("Fireteam on Fire", 3000),
            ("First Try", 3000),
            
            ]
    
            army_qualifications = [
                ("Scout Trooper", 3000),
            ("Aerial Trooper", 2500),
            ("Engineer", 2500),
            ("Ace Pilot", 3000),
            ("ARF Trooper", 2000),
            ("Interceptor Pilot", 2000),
            ("Bomber Pilot", 2000),
            ("Veteran Trooper", 2000),
            ("Strike Cadre", 3000),
            ("Juggernaut Cadre", 3000),
            ("Shadow Cadre", 3000),
            ("ARC Qualification", 20000),
            ("Republic Commando", 23000),
            ("Frontliner", 2000),
            ("Submachine Gunner", 1500),
            ("Rifleman", 1500),
            ("CQC Trooper", 1500),
            ("Suppressor", 1000),
            ("Grenadier", 1500),
            ("Heavy Rifleman", 2000),
            ("Hunter", 1000),
            ("Aggressor", 1500),
            ("Sniper", 2000),
            ("Slug Shooter", 1000),
            ("Sharpshooter", 1500),
            ("Operative", 1000),
            ("Urban Warrior", 1500),
            ("Gunslinger", 1000),
            ("HERO Pilot - First Class", 8000),
            ("HERO Pilot - Second Class", 4000),
            ("Galactic Marine", 3000),
            ("Medic Cadre", 3000),
            ("Shadow Pilot", 8000),
            ("Sapper", 2500),
            ("Sky Trooper", 5000)
            ]
    
            navy_qualifications = [
                ("Interceptor Qualification", 2000),
            ("Bomber Qualification", 2000),
            ("Ace Pilot", 3000),
            ("HERO - Dogfighter", 4000),
            ("HERO - Objective", 4000),
            ("HERO - Aerial Denial", 4000),
            ("HERO - Mobility", 4000),
            ("HERO - Support", 4000)
            ]
    
            sof_medals = [
                ("SOF Service Medal", 3000),
            ("Special Forces Veteran", 1500),
            ("Special Forces Legend", 2000),
            ("Special Forces Myth", 2500),
            ("Unexpected Assistance", 2000),
            ("Devout Protector", 2500),
            ("Strength in Unity", 2000),
            ("Brotherhood of Steel", 2500),
            ("Brothers in Arms", 2000),
            ("Proven Advisor", 3000),
            ("Impossible Odds", 2000),
            ("41st Superiority", 2000),
            ("Double The Effort", 2000),
            ("Regime Toppler", 3500),
            ("Survivalist", 2000),
            ("Unbreakable", 2000),
            ("Republic Juggernaut", 2000),
            ("Death From Above", 2000),
            ("Furry Frenzy", 2000),
            ("Back to Basics", 2000),
            ("Operation:SuppressiveShrout", 1000),
            ("Seasoned Saboteur", 1250),
            ("Support Scuttler", 1750),
            ("Masterful Saboteur", 2250),
            ("In And Out", 2000),
            ("Superior Tactics", 2750),
            ("Safety's Off", 2000),
            ("Tinnie Scrapper", 2250),
            ("Commando Culler", 2500),
            ("Guerrilla Tactician", 2250),
            ("Unwavering", 1750),
            ("Guardian Angel", 1000)
            ]
    
            regiment_medals = [
                ("Fixer Upper", 1500),
            ("Behind Enemy Lines", 1500),
            ("Above and Beyond", 1500),
            ("Devout Protectors", 1500),
            ("Altered Genetics", 1500),
            ("Dragway Genetics", 1500),
            ("Perfect Attendance", 2500),
            ("Honor Roll", 3500),
            ("All Terrain Terror", 2500),
            ("The Team to Beat", 1500),
            ("Leading to Victory", 2500),
            ("To Sacrifice and Serve", 2000),
            ("For the Republic", 1000),
            ("Dedication is Key", 5000),
            ("Squad Oriented", 2000),
            ("All but Special Forces", 1000),
            ("Top Trainer", 1500),
            ("Leading the Charge", 2500),
            ("Participation Trophy", 1500),
            ("A Cut Above", 1000),
            ("Base Class Champion", 2500),
            ("Trials are our Speciality", 1500),
            ("Team Player", 3000),
            ("Old but Gold", 1500),
            ("He's going for Speed", 2500),
            ("He's Going the Distance", 1000),
            ("Basic Equipment Expert", 2000),
            ("Praise the Maker", 1500),
            ("FEEL THE WRATH OF THE 41ST", 1000),
            ]
    
            # Get medals and qualifications from specific servers
            army_server = self.bot.get_guild( 850840453800919100)
            army_roles, level_roles, army_qual_roles, navy_qual_roles = [], [], [], []
            if army_server:
                army_member = army_server.get_member(user.id)
                if army_member:
                    army_roles = [role.name for role in army_member.roles for (x, y) in army_medals if role.name == x]
                    army_credits = [y for role in army_member.roles for (x, y) in army_medals if role.name == x]
                    army_roles_f = "\n".join(f"{role} {credit}" for role, credit in zip(army_roles, army_credits))
    
                    level_roles = [role.name for role in army_member.roles for (x, y) in level_medals if role.name == x]
                    level_credits = [y for role in army_member.roles for (x, y) in level_medals if role.name == x]
                    level_roles_f = "\n".join(f"{role} {credit}" for role, credit in zip(level_roles, level_credits))
    
                    army_qual_roles = [role.name for role in army_member.roles for (x, y) in army_qualifications if role.name == x]
                    army_qual_credits = [y for role in army_member.roles for (x, y) in army_qualifications if role.name == x]
                    army_qual_roles_f = "\n".join(f"{role} {credit}" for role, credit in zip(army_qual_roles, army_qual_credits))
    
                    navy_qual_roles = [role.name for role in army_member.roles for (x, y) in navy_qualifications if role.name == x]
                    navy_qual_credits = [y for role in army_member.roles for (x, y) in navy_qualifications if role.name == x]
                    navy_qual_roles_f = "\n".join(
                        f"{role} {credit}" for role, credit in zip(navy_qual_roles, navy_qual_credits))
    
            sof_server = self.bot.get_guild(911409562970628167)
            sof_roles = []
            if sof_server:
                sof_member = sof_server.get_member(user.id)
                if sof_member:
                    sof_roles = [role.name for role in sof_member.roles for (x, y) in sof_medals if role.name == x]
                    sof_credits = [y for role in sof_member.roles for (x, y) in sof_medals if role.name == x]
                    sof_roles_f = "\n".join(f"{role} {credit}" for role, credit in zip(sof_roles, sof_credits))
    
            regiment_server = self.bot.get_guild(1138926753931346090)
            regiment_roles = []
            if regiment_server:
                regiment_member = regiment_server.get_member(user.id)
                if regiment_member:
                    regiment_roles = [role.name for role in regiment_member.roles for (x, y) in regiment_medals if
                                      role.name == x]
                    regiment_credits = [y for role in regiment_member.roles for (x, y) in regiment_medals if role.name == x]
                    regiment_roles_f = "\n".join(
                        f"{role} {credit}" for role, credit in zip(regiment_roles, regiment_credits))
    
            #Prepare the embed
            embed = discord.Embed(title="Your Breakdown", color=discord.Color.orange())
    
            embed.add_field(name="Username", value=user.display_name, inline=False)
            embed.add_field(name="Army Rank", value=army_rank, inline=False)
            embed.add_field(name="Current Credits", value=current_credits, inline=False)
    
            if army_roles:
                embed.add_field(name="Army Medals", value=army_roles_f, inline=False)
            if level_roles:
                embed.add_field(name="Level Medals", value="".join(level_roles_f), inline=False)
            if army_qual_roles:
                embed.add_field(name="Army Qualifications", value="".join(army_qual_roles_f), inline=False)
            if navy_qual_roles:
                embed.add_field(name="Navy Qualifications", value="".join(navy_qual_roles_f), inline=False)
            if sof_roles:
                embed.add_field(name="SOF Medals", value="".join(sof_roles_f), inline=False)
            if regiment_roles:
                embed.add_field(name="Regiment Medals", value="".join(regiment_roles_f), inline=False)
    
            embed.add_field(name="Max Credits", value=max_credits, inline=False)
    
            embed.add_field(name="Your Rank Rewards", value=rewards_message, inline=False)
    
            if purchases_list:
                purchases_str = purchases_list_f
                embed.add_field(name="Your Purchases", value=purchases_str, inline=False)
            else:
                embed.add_field(name="Your Purchases", value="You have no purchases.", inline=False)
    
            embed.add_field(name="Removed Credits", value=removed_credits, inline=False)
    
            await ctx.send(embed=embed)
    
        else:
            embed = discord.Embed(
                title="Whoami Command",
                description=f"Use one of the following subcommands:\n"
                            f"!whoami medals - to see your medals\n"
                            f"!whoami purchases - to see your purchases\n"
                            f"!whoami stats - to see your stats\n"
                            f"!whoami credits - to see the full breakdown of your credits",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def uptime(self, ctx):
        uptime_duration = datetime.now() - start_time
        await ctx.send(f"Bot has been running for {uptime_duration}")

    @commands.command(name='show_quals')
    @is_allowed_channel()
    @commands.has_any_role('SOF Staff')
    @commands.check(is_registered)
    async def show_qualifications(self, ctx):
        # Define server IDs
        server_with_users = 1138926753931346090  # Server ID where users should be checked
        server_with_qualifications = 850840453800919100  # Server ID where qualifications are stored
    
        # Get the guilds (servers)
        guild_with_users = self.bot.get_guild(server_with_users)
        guild_with_qualifications = self.bot.get_guild(server_with_qualifications)
    
        if not guild_with_users or not guild_with_qualifications:
            await ctx.send("One or both of the servers are not accessible.")
            return
    
        # Dictionary to store qualifications with corresponding users by platform
        qualifications_by_platform = {"PC": {}, "Xbox": {}, "PS": {}}
    
        # Iterate over members in the first server
        for member in guild_with_users.members:
            # Determine the user's main platform
            main_platform = None
            for role in member.roles:
                if role.name in main_platform_roles:
                    main_platform = main_platform_roles[role.name]
                    break  # Main platform found, no need to check further
    
            if not main_platform:
                continue  # Skip users without a main platform role
    
            # Check if the user is also in the qualifications server
            member_in_qualifications_guild = guild_with_qualifications.get_member(member.id)
            if member_in_qualifications_guild:
                # Iterate over the member's roles in the qualifications server
                for role in member_in_qualifications_guild.roles:
                    # Check for Army qualifications
                    if role.name in army_qualifications:
                        if role.name not in qualifications_by_platform[main_platform]:
                            qualifications_by_platform[main_platform][role.name] = []
                        qualifications_by_platform[main_platform][role.name].append(member.display_name)
                    # Check for Advanced Weaponry qualifications
                    elif role.name in advanced_weaponry_qualifications:
                        if "Advanced Weaponry" not in qualifications_by_platform[main_platform]:
                            qualifications_by_platform[main_platform]["Advanced Weaponry"] = {}
                        if role.name not in qualifications_by_platform[main_platform]["Advanced Weaponry"]:
                            qualifications_by_platform[main_platform]["Advanced Weaponry"][role.name] = []
                        qualifications_by_platform[main_platform]["Advanced Weaponry"][role.name].append(
                            member.display_name)
    
        # Create the output message
        output_message = ""
    
        for platform, qualifications_dict in qualifications_by_platform.items():
            output_message += f"\n**{platform} Users**:\n"
    
            # If there are Advanced Weaponry qualifications
            if "Advanced Weaponry" in qualifications_dict:
                output_message += f"\n**Advanced Weaponry**:\n"
                for sub_qualification, sub_users in qualifications_dict["Advanced Weaponry"].items():
                    output_message += f"\n*{sub_qualification}*:\n"
                    for user in sub_users:
                        output_message += f"- {user}\n"
    
            # Non-Advanced Weaponry qualifications
            for qualification, users in qualifications_dict.items():
                if qualification == "Advanced Weaponry":
                    continue  # Skip since already handled above
                output_message += f"\n**{qualification}**:\n"
                for user in users:
                    output_message += f"- {user}\n"
    
        # Send the output in chunks if it's too long
        await send_long_message(ctx,
                                output_message if output_message else "No users with the specified qualifications found.")

    @commands.command()
    @commands.has_any_role('Economy Admin', 'Economy Lead', 'Commander', 'Technical Commander', 'Staff Sergeant', 'Sergeant Major', '2nd Lieutenant', 'Lieutenant', 'Captain', 'Major', 'High Command')
    @commands.check(is_registered)
    async def ct_number(self, ctx):
    
        file_path = '/home/dominik/Downloads/41st CT Numbers.txt'
        existing_numbers = set()
    
        # Lese die bestehenden CT-Nummern aus der Datei
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith('PLEASE ADD'):  # Überspringe die Überschrift
                    continue
                numbers = line.split(', ')
                existing_numbers.update(int(number) for number in numbers if number.isdigit())
    
        # Generiere eine neue, nicht verwendete CT-Nummer
        new_number = None
        while not new_number or new_number in existing_numbers:
            new_number = random.randint(1000, 9999)
    
        # Füge die neue Nummer zur Datei hinzu
        with open(file_path, 'a') as file:
            file.write(f'{new_number}, ')
    
        # Sende eine Nachricht mit der neuen Nummer an den Benutzer
        embed = discord.Embed(
            title="New CT Number Generated",
            description=f"Your new CT number is: **{new_number}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def rules(self, ctx, category: int = None):
        rules_categories = {
    
            1: (
    
                "Army Raid Rules:\n"
    
                "All members involved in a raid are required to participate by the following rules, regardless of MilSim status.\n"
    
                "1) Raid Leaders are in full command during raids. Follow their instructions to the best of your ability. "
    
                "If you hear a raid leader state \"Clear Comms\", stop talking and listen to their instructions.\n"
    
                "2) Refrain from screeching into the mic. Keep communications clear when using tact-comms.\n"
    
                "3) All clones must use their default clone-wars era weaponry. All star cards are allowed. Default weaponry as follows:\n"
    
                "  - DC-15A for Assault\n"
    
                "  - DC-15 or DC-15 LE for Heavy (All attachments acceptable for DC-15 LE)\n"
    
                "  - DC-17 for Officer\n"
    
                "  - Valken-38x for Specialist\n"
    
                "4) Officer may only be used by troopers of the rank Sergeant or above.\n"
    
                "5) No trooper may utilize reinforcements or non-base weapons without having earned the related qualification. "
    
                "This includes Aerial, Infiltrator, Enforcer, Tank, the AT-TE, and AT-RT. Speeder bikes are allowed on both droids and clones. "
    
                "You must earn the right to use these classes. In addition, we are a clone MilSim, we do not use heroes.\n"
    
                "6) Raid Leaders of SGT+ may host special raids with alternative rulesets. SGT+ troopers have earned trust from high command "
    
                "and may alter the ruleset AT THE BEGINNING OF THE RAID if they so choose. Raid rules may NEVER be changed once a match has started. "
    
                "Alternative rulesets are only allowed in the main server, squad raids, or events."
    
            ),
    
            2: (
    
                "Skin Rules:\n"
    
                "All members of any 41st regiment are expected to follow these rules while in any 41st event, regardless of raid rules.\n"
    
                "- Default \"Shiny\": Cadets Only\n"
    
                "- Phase 2 41st Elite Corps: Clone Troopers\n"
    
                "- 41st Ranger Platoon: CTVs\n"
    
                "- 41st Scout Battalion: Scout Troopers\n"
    
                "- All Aerial skins: Aerial Troopers\n"
    
                "- Phase 1 41st Elite Corps: Troopers who purchase phase 1 with credits or payment.\n"
    
                "- 212th ARF: ARF Troopers\n"
    
                "- BARC Trooper: Troopers who purchase the BARC Trooper helmet with credits or payment\n"
    
                "- Engineers: 181st Armor Division"
    
            ),
    
            3: (
    
                "Geetsly's 41st Elite Corps Server Guidelines:\n"
    
                "By participating in Geetsly's 41st Elite Corps or any of its affiliated servers, you agree to abide by all the rules listed below.\n"
    
                "Refusal to follow the rules or failing to follow staff instructions can lead to punishment leading up to a permanent ban.\n"
    
            ),
    
            4: (
    
                "41st Community Rules:\n"
    
                "1) Follow Discord's Terms of Service: https://discord.com/terms\n"
    
                "2) Please use English in Geetsly's 41st and its affiliated servers.\n"
    
                "3) Promotion of other discord communities is prohibited without direct approval.\n"
    
                "4) Harassment of fellow members is not tolerated.\n"
    
                "5) Treat other communities and individuals with respect.\n"
    
                "6) Staff members regularly monitor chats.\n"
    
                "7) Sexually explicit content, excessive gore, or animal cruelty are banned.\n"
    
                "8) You must be 13 years of age to participate.\n"
    
            ),
    
            5: (
    
                "Unruly Behavior Guidelines:\n"
    
                "These guidelines govern the use of jokes, quips, and friendly insults within the 41st Elite Corps.\n"
    
                "1) Stop your conversation immediately if requested by any member of the community.\n"
    
                "2) Topics such as Racism, Sexism, Suicide, Sexual Themes, Misogyny, or Hate Speech will result in disciplinary action.\n"
    
                "3) Utilizing banned topics may lead to a timeout or ban.\n"
    
                "4) Avoid edgy topics even if meant as a joke.\n"
    
            ),
    
            6: (
    
                "Staff Expectations:\n"
    
                "All staff are expected to reach 3 attendance and host a minimum of 2 raids per attendance period.\n"
    
            ),
    
            7: (
    
                "Hosting a Raid:\n"
    
                "To host a raid, speak with your squadmates to determine a suitable time.\n"
    
                "Announce the raid with a lore-friendly blurb and include the raid gif.\n"
    
                "Raids must last at least 45 minutes. If shorter, a third game must be played.\n"
    
                "Host raids in the appropriate raid channels. Notify with the correct tags.\n"
    
            ),
    
            8: (
    
                "Running a Raid:\n"
    
                "Keep the raid on-track, giving orders as necessary.\n"
    
                "Use 'Clear Comms' to regain control when needed.\n"
    
                "Report unruly behavior to higher staff.\n"
    
            ),
    
            9: (
    
                "Emergency Situations:\n"
    
                "Main server staff can remove members exhibiting extreme behavior immediately.\n"
    
                "Report all emergencies to a High Command member for further actions.\n"
    
            ),
    
            10: (
            "Rank Hierarchy:\n"
            "Follow orders based on the rank hierarchy.\n"
            "If someone's rank is higher than yours, they have authority over you.\n"
            "- High Command\n"
            "- Marshall Commander\n"
            "- Commander = RC Commander = ARC Commander = Technical Commander\n"
            "- Major\n"
            "- Captain = RC Captain = ARC Captain\n"
            "- Lieutenant = ARC Lieutenant = RC Lieutenant\n"
            "- 2nd Lieutenant\n"
            "- Sergeant Major = RC Sergeant = ARC Sergeant\n"
            "- Staff Sergeant\n"
            "- Sergeant = ARC = RC\n"
            "- Corporal\n"
            "- Lance Corporal\n"
            "- Clone Trooper"
    
    
    
    
        ),
    
            11: (
    
                "Strike System + Discipline:\n"
    
                "Breaking rules can lead to disciplinary-reports and strikes.\n"
    
                "Three strikes lead to permanent removal.\n"
    
                "Strikes expire after six months.\n"
    
                "The strike system applies to all ranks.\n"
    
            ),
    
        }
    
        if category is None:
    
            embed = discord.Embed(
    
                title="41st Elite Corps Rules Categories",
    
                description="Please choose a category by using !rules <number>.\n\n"
    
                            "1 - Army Raid Rules\n"
    
                            "2 - Skin Rules\n"
    
                            "3 - Server Guidelines\n"
    
                            "4 - Community Rules\n"
    
                            "5 - Unruly Behavior Guidelines\n"
    
                            "6 - Staff Expectations\n"
    
                            "7 - Hosting a Raid\n"
    
                            "8 - Running a Raid\n"
    
                            "9 - Emergency Situations\n"
    
                            "10 - Rank Hierarchy\n"
    
                            "11 - Strike System + Discipline",
    
                color=discord.Color.green()
    
            )
    
            await ctx.send(embed=embed)
    
        elif category in rules_categories:
    
            embed = discord.Embed(
    
                title=f"41st Elite Corps Rules - Category {category}",
    
                description=rules_categories[category],
    
                color=discord.Color.blue()
    
            )
    
            await ctx.send(embed=embed)
    
        else:
    
            await ctx.send("Invalid category. Please use a number between 1 and 11.")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def helmets(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
    
        # Get user roles, rank, and purchases
        user_roles = {role.name for role in member.roles}
        user_purchases = get_user_purchases(member.id)
        rank = None
        for role in user_roles:
            if role in ["High Command", "Marshall Commander", "Commander", "Major", "Captain", "Lieutenant", "2nd Lieutenant", "Sergeant Major", "Staff Sergeant", "Sergeant"]:
                rank = role
                break
    
        # Define helmet and attachment options
        helmet_options = {
            "Assault Trooper": "Base Assault Helmet",
            "Heavy Trooper": "Base Heavy Helmet",
            "Specialist Trooper": "Base Specialist Helmet",
            "Engineer": "Engineer Helmet",
            "Aerial Trooper": "Airborne Helmet",
            "ARF Trooper": "AT-RT Driver (ARF)",
            "Credit purchase": ["ARF P1 Helmet (ARF)", "BARC Helmet", "Cold Assault Helmet", "Phase 1 Helmet", "Heavy GunnerHeavy", "Desert Helmet"],
            "Strike cadre": "Spec Ops P1",
            "Medic Cadre": "Medic Cadre",
            "Shadow Cadre": "Shadow Cadre",
            "Juggernaut Cadre": "Juggernaut Cadre",
            "Galactic Marine": "Galactic Marine",
            "Scout Trooper": "Scout",
            "Sky Trooper": "Skytrooper",
            "ARC Trooper": "ARC Helmet",
            "Republic Commando": "RC Helmet"
        }
    
        # Correct helmet names for credit purchases
        purchase_mappings = {
            "Clone Gunner": "Heavy GunnerHeavy",
            "Snowtrooper/Flametrooper": "Cold Assault Helmet",
            "BARC": "BARC Helmet",
            "Phase 1": "Phase 1 Helmet",
            "Desert": "Desert Helmet",
            "ARF": "ARF P1 Helmet (ARF)"
        }
    
        # Adjust user purchases based on mappings
        user_purchases = [purchase_mappings.get(item, item) for item in user_purchases]
    
        attachment_options = {
            "Base Assault Helmet": [
                "Heavy Sun Blinders and Top Attachments (Heavy, free)",
                "Specialist Visor Down (Specialist, free)",
                "Specialist Visor Up (Specialist)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Tubes (credits)",
                "Hood (Shadow, SOF)"
            ],
            "Base Heavy Helmet": [
                "Heavy Sun Blinders and Top Attachments (Heavy, free)",
                "Specialist Visor Down (Specialist, free)",
                "Specialist Visor Up (Specialist)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Tubes (credits)",
                "Hood (Shadow, SOF)"
            ],
            "Base Specialist Helmet": [
                "Heavy Sun Blinders and Top Attachments (Heavy, free)",
                "Specialist Visor Down (Specialist, free)",
                "Specialist Visor Up (Specialist)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Tubes (credits)",
                "Hood (Shadow, SOF)"
            ],
            "Engineer Helmet": [
                "Officer Antenna (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Tubes (credits)",
                "Hood (Shadow)"
            ],
            "Airborne Helmet": [
                "Officer Antenna (SGT+, free)",
                "Heavy Sun Blinders and Top Attachments (Heavy)",
                "Specialist Visor Down (Specialist)",
                "Specialist Visor Up (Specialist)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Hood (Shadow)"
            ],
            "AT-RT Driver (ARF)": [
                "Officer Antenna (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Tubes (credits)",
                "Hood (Shadow)"
            ],
            "ARF P1 Helmet (ARF)": [
                "Flaps (free)",
                "Officer Antenna (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Tubes (credits)",
                "Hood (Shadow)"
            ],
            "BARC Helmet": [
                "Heavy Sun Blinders and Top Attachments (Heavy)",
                "Specialist Visor Down (Specialist)",
                "Specialist Visor Up (Specialist)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Hood (Shadow, SOF)"
            ],
            "Cold Assault Helmet": [
                "Officer Antenna (SGT+, free)",
                "Heavy Top Attachments (Heavy)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Tubes (credits)",
                "Hood (Shadow, SOF)"
            ],
            "Heavy GunnerHeavy": [
                "Sun Blinders (Heavy)",
                "Specialist Visor Down (Specialist)",
                "Specialist Visor Up (Specialist)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Tubes (credits)",
                "Hood (Shadow, SOF)"
            ],
            "Spec Ops P1": [
                "Officer Antenna (SGT+, free)"
            ],
            "Juggernaut Cadre": [
                "Officer Antenna (SGT+, free)",
                "Heavy Top Attachments (Heavy)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Tubes (credits)"
            ],
            "Medic Cadre": [
                "Visor Down (credits)",
                "Medic Cadre Visor Up (credits)",
                "Heavy Sun Blinders and Top Attachments (Heavy)",
                "Specialist Visor Down (Specialist)",
                "Specialist Visor Up (Specialist)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Tubes (credits)",
                "Hood (Shadow, SOF)"
            ],
            "Shadow Cadre": [
                "Heavy Sun Blinders and Top Attachments (Heavy)",
                "Specialist Visor Down (free)",
                "Specialist Visor Up (Specialist)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Tubes (credits)",
                "Hood (free)"
            ],
            "Phase 1 Helmet": [
                "Heavy Sun Blinders (Heavy)",
                "Specialist Visor Down (Specialist)",
                "Specialist Visor Up (Specialist)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits, incompatible with rangefinder)",
                "Floodlight (credits, requires heavy sun blinders)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Hood (Shadow)"
            ],
            "Galactic Marine": [
                "Officer Antenna (SGT+, free)",
                "Heavy Top Attachments (Heavy)",
                "Antenna (credits)",
                "Floodlight (credits)"
            ],
            "Scout": [
                "Officer Antenna (SGT+, free)",
                "Heavy Top Attachments (Heavy)",
                "Antenna (credits)",
                "Tubes (credits)",
                "Hood (Shadow)"
            ],
            "Skytrooper": [
                "Heavy Top Attachments (Heavy)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Hood (Shadow)"
            ],
            "Desert Helmet": [
                "Heavy Sun Blinders and Top Attachments (Heavy)",
                "Rangefinder (SGT+, free)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (SGT+)",
                "Tubes (credits)",
                "Hood (Shadow, SOF)"
            ],
            "ARC Helmet": [
                "Heavy Sun Blinders and Top Attachments (credits)",
                "Specialist Visor Down (credits)",
                "Specialist Visor Up (credits)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (credits)",
                "Tubes (credits)",
                "Hood (credits)"
            ],
            "RC Helmet": [
                "Heavy Sun Blinders and Top Attachments (credits)",
                "Specialist Visor Down (credits)",
                "Specialist Visor Up (credits)",
                "Antenna (credits)",
                "Floodlight (credits)",
                "Communicator (credits)",
                "Rangefinder Down (credits)",
                "Hood (credits)"
            ]
        }
    
        # Determine eligible helmets and attachments
        eligible_helmets = {}
    
        # Include helmets from user purchases directly in eligible helmets
        for purchase in user_purchases:
            if purchase in helmet_options["Credit purchase"]:
                eligible_helmets[purchase] = []
    
        for role, helmet in helmet_options.items():
            if role in user_roles:
                if isinstance(helmet, list):
                    for h in helmet:
                        eligible_helmets[h] = []
                else:
                    eligible_helmets[helmet] = []
    
        for helmet in eligible_helmets.keys():
            if helmet in attachment_options:
                for attachment in attachment_options[helmet]:
                    if "(SGT+" in attachment and rank not in ["Sergeant", "Staff Sergeant", "Sergeant Major", "2nd Lieutenant", "Lieutenant", "Captain", "Major", "Commander", "High Command"]:
                        continue  # Skip attachments not allowed for lower ranks
                    if "(credits)" in attachment and attachment not in user_purchases:
                        continue  # Skip if the user hasn't bought this item with credits
                    eligible_helmets[helmet].append(attachment)
    
        # Create an embed message with eligible helmets and attachments
        embed = discord.Embed(title="Eligible Helmets and Attachments", color=discord.Color.blue())
        for helmet, attachments in eligible_helmets.items():
            attachment_list = "\n".join(attachments) if attachments else "No available attachments"
            embed.add_field(name=f"{helmet}", value=attachment_list, inline=False)
    
        # Send the embed message in the channel
        await ctx.send(embed=embed)
    
        print(f"Sent helmet and attachment options to {member.display_name} ({member.id}).")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def ranks(self, ctx, rank_number: int = None):
        rank_list = [
            "High Command",
            "Marshall Commander",
            "Technical Commander",
            "Commander / RC Commander / ARC Commander",
            "Major",
            "Captain",
            "Lieutenant",
            "2nd Lieutenant",
            "Sergeant Major",
            "Staff Sergeant",
            "Sergeant",
            "Corporal",
            "Lance Corporal",
            "Clone Trooper"
        ]
    
        rank_descriptions = [
            "The leader of their respective platform or Creative Team and overall command of the server.",
            "Overall command of the server.",
            "Commander of the technical side (logistics, bot).",
            "Commander of the army, Republic Commandos, or ARC Troopers. All of these ranks share the same power and authority level.",
            "Overall command of the server, directly under the rank of Commander.",
            "Leader of their respective platform.",
            "In command of their troopers directly under their Captain.",
            "In command of their Platoons, directly under their Lieutenant.",
            "Leader of their Platoon and Squads, directly under their 2nd Lieutenant, Lieutenant, and Captain.",
            "Leader of their Squad, helping hand for their Sergeant Major.",
            "Leader of their Squad, under the command of their Staff Sergeant and Sergeant Major.",
            "Co-squad leader with their Sergeant / Staff Sergeant.",
            "Leader of their fire team.",
            "Part of a fire team in a Squad."
        ]
    
        if rank_number is None:
            # Send the list of ranks with numbers, highest at the top in an embed
            rank_text = "\n".join(f"{i + 1}. {rank}" for i, rank in enumerate(rank_list))
            embed = discord.Embed(
                title="41st Rank Hierarchy (Highest to Lowest) \n To view details of a specific rank, use !ranks <number>.",
                description=rank_text,
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Note",
                value="If ranks are grouped (e.g., 'Commander / RC Commander / ARC Commander'), they have equal authority.",
                inline=False
            )
            embed.set_footer(text=".")
            await ctx.send(embed=embed)
        elif 1 <= rank_number <= len(rank_list):
            # Send the description of the requested rank in an embed
            rank_index = rank_number - 1
            rank_name = rank_list[rank_index]
            rank_description = rank_descriptions[rank_index]
    
            embed = discord.Embed(
                title=f"Rank: {rank_name}",
                description=rank_description,
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            # Send an error message if the rank number is invalid
            embed = discord.Embed(
                title="Invalid Rank Number",
                description="Please use a number between 1 and 14.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
        print(f"Sent rank information to {ctx.author.display_name} ({ctx.author.id}).")

async def setup(bot):
    await bot.add_cog(Utility(bot))
