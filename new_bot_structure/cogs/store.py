import discord
from discord.ext import commands
import asyncio
import random
from utils import *
from database import *

class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def ggn_store(self, ctx):
        store_info = (
            "`Geetsly's Gaming Network Store Conversions:`\n"
            "(Please note that these are not prices for credit values. These are credit value conversions, "
            "meaning that a store item which is 15,000 credits is purchasable with $12.50 USD.)\n\n"
            "credits: `7,500` - `$5.00 USD`\n"
            "credits: `10,000` - `$7.50 USD`\n"
            "credits: `12,500` - `$10.00 USD`\n"
            "credits: `15,000` - `$12.50 USD`\n"
            "credits: `20,000` - `$15.00 USD`\n"
            "credits: `25,000` - `$20.00 USD`\n"
            "credits: `30,000` - `$25.00 USD`\n"
            "credits: `40,000` - ``$30.00 USD`\n"
            "credits: `45,000` - `$30.00 USD`\n\n"
            "**EXCEPTIONS/SPECIFICS:**\n"
            "'Phase-1 In Game' - `$10.00 USD`\n"
            "'Custom Visor' - `$15.00 USD`\n"
            "'2003 Helmet' - `$20.00 USD`"
        )
        additional_info = (
            "Please remember to DM 'Forceps' CC-3432 for any GGN-Store purchases."
        )
        embed = discord.Embed(
            description=f'{store_info}\n\n{additional_info}',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def store(self, ctx, category: int = None):
        store_categories = {
            1: (
                "credits: ```7,500``` - ```$5.00 USD```\n"
                "7,500 - 'Helmet Attachments'\n"
                "Choose from one of our pre-existing helmet attachment options. These options currently include: Flashlights, Antennas, Communicators, and the Heavy Sunvisor.\n"
                "7,500 - 'Rangefinder Down'\n"
                "A Rangefinder lowered over the eyes. (For SGT+ only.)\n"
                "7,500 - 'Helmet Tubes/Pipes'\n"
                "Adds some tubes to your helmet so you can survive without oxygen for a while. "
            ),
            2: (
                "credits: ```10,000``` - ```$7.50 USD```\n"
                "10,000 - 'Build-Your-Own Attachment'\n"
                "A custom attachment brainstormed by you, built by the Art Team Leads. NOTE: Your attachment can not resemble other attachments, such as a rangefinder.\n"
                "10,000 - 'Specialist Binoculars'\n"
                "Allows for binoculars to be added to your helmet. NOTE: Not all helmets are compatible.\n"
                "10,000 - 'Specialist Binoculars Up'\n"
                "Allows for raised binoculars. NOTE: You must already have access to the binoculars."
            ),
            3: (
                "credits: ```15,000``` - ```$10.00 USD```\n"
                "15,000 - 'Flight Computer/Targeting Visor'\n"
                "An external holographic visor. (The Flight Computer is only available to ACE pilots of SGT+. The Targeting Visor is only available to Strike Cadre and Medic Cadre helmets.\n"
                "20,000 - 'Clone Gunner Helmet'\n"
                "A new helmet template. Google 'Clone Heavy Gunner' for reference.\n"
                "20,000 - 'Hooded Helmet'\n"
                "Stylish and Sneaky. (Only for SOF.)"
            ),
            4: (
                "credits: ```30,000``` - ```$25.00 USD```\n"
                "30,000 - 'Phase 1 ARF Helmet'\n"
                "The ARF Helmet from 'Star Wars The Clone Wars' Only for ARF Trooper or SOF .\n"
                "30,000 - 'Snowtrooper/Flametrooper Helmet'\n"
                "BRING IN THE FLAMETHROWERS!\n"
                "30,000 - 'Custom Visor'\n"
                "Clearance to a one color visor. NOTE: Troopers may get a refund upon reaching the rank of 2LT or higher, or RC.\n"
                "30,000 - 'Render'\n"
                "Gives you only the ability to wear a render. The actual render will not be included.The render has to be submitted for approval\n"
                "35,000 - 'BARC Helmet and Skin'\n"
                "'For the mysterious types.' Receive access to the 41st BARC Helmet as well as permission to use the 91st Recon Corps in game.\n"
                "35,000 - 'Phase 1 Helmet and Skin'\n"
                "A Phase 1 helmet, along with clearance to wear the corresponding skin in game."
            ),
            5: (
                "credits: ```40,000``` - ```$30.00 USD```\n"
                "40,000 - '2003 Helmet Variants'\n"
                "The classic style. Available for all helmet templates.\n"
                "45,000 - 'Desert Trooper Helmet (And Skin for PC Only.)'\n"
                "'I hate sand.' Receive the 41st Desert Trooper Helmet as well as access to the 501st Legion in game, if you are on PC. NOTE: Google Clone Desert Trooper for a reference.\n"
                "50,000- 'Halfbody art piece'"
            )
    
        }
    
        async def send_dm(content):
            max_length = 2000
            for i in range(0, len(content), max_length):
                await ctx.author.send(content[i:i + max_length])
    
        if category is None:
            summary = (
                "Please use the extended command `!store #` to view all the items in each price category. Here is a key:\n"
                "```\n"
                " 07,500 - !store 1\n"
                " 10,000 - !store 2\n"
                " 15,000 - !store 3\n"
                " 30,000 - !store 4\n"
                " 40,000 - !store 5\n"
                " !store 0 to see all"
                "```\n"
            )
    
            embed = discord.Embed(
                title="Store Categories",
                description=summary,
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif category == 0:
            all_store_info = "\n\n".join(store_categories.values())
            await send_dm(all_store_info)
            embed = discord.Embed(
                title="Store Categories",
                description="I have sent you a DM with all the store categories.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif category in store_categories:
            embed = discord.Embed(
                title=f"Store Category {category}",
                description=store_categories[category],
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Invalid Category",
                description="Invalid category. Please use a number between 0 and 5.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def purchase(self, ctx, *, item_name: str = None):
        # Define the items_list here
        items_list = "\n".join(store_items.keys())
    
        if item_name is None:
            message = (
                "To purchase an item, use the command `!purchase <Item name>`.\n"
                "For more information, use `!store`.\n\n"
                "**Available items:**\n"
                f"{items_list}"
            )
            await ctx.send(message)
            return
    
        user_id = ctx.author.id
        current_credits = get_user_credits(user_id, ctx.author.roles, role_credits, non_stacking_roles)[0]
    
        if item_name not in store_items:
            await ctx.send(f"The item '{item_name}' is not available in the store.")
            return
    
        # Check if the user has already purchased the item
        purchased_items = get_user_purchases(user_id)
        if item_name in purchased_items:
            await ctx.send(f"You have already purchased '{item_name}' and cannot buy it again.")
            return
    
        item_price = store_items[item_name]
    
        if current_credits >= item_price:
            # Deduct the item price from user's credits
            new_credits = current_credits - item_price
            update_user_credits(user_id, new_credits)
            add_user_purchase(user_id, item_name)
            await ctx.send(
                f"You have successfully purchased '{item_name}' for {item_price} credits. New balance: {new_credits} credits.")
        else:
            await ctx.send(
                f"You do not have enough credits to purchase '{item_name}'. You need {item_price - current_credits} more credits.")

    @commands.command()
    @commands.has_any_role('Economy Lead', 'Commander', 'Technical Commander')
    @commands.check(is_registered)
    async def buy(self, ctx, user: discord.Member, *, item_name: str = None):
        # Define the items_list here
        items_list = "\n".join(store_items.keys())
    
        if item_name is None:
            message = (
                "To purchase an item, use the command `!purchase <@User> <Item name>`.\n"
                "For more information, use `!store`.\n\n"
                "**Available items:**\n"
                f"{items_list}"
            )
            await ctx.send(message)
            return
    
        user_id = user.id
        current_credits = get_user_credits(user_id, user.roles, role_credits, non_stacking_roles)[0]
    
        if item_name not in store_items:
            await ctx.send(f"The item '{item_name}' is not available in the store.")
            return
    
        # Check if the user has already purchased the item
        purchased_items = get_user_purchases(user_id)
        if item_name in purchased_items:
            await ctx.send(f"{user.mention} has already purchased '{item_name}' and cannot buy it again.")
            return
    
        item_price = store_items[item_name]
    
        if current_credits >= item_price:
            # Deduct the item price from user's credits
            new_credits = current_credits - item_price
            update_user_credits(user_id, new_credits)
            add_user_purchase(user_id, item_name)
            await ctx.send(
                f"{user.mention} has successfully purchased '{item_name}' for {item_price} credits. New balance: {new_credits} credits.")
        else:
            await ctx.send(
                f"{user.mention} does not have enough credits to purchase '{item_name}'. They need {item_price - current_credits} more credits.")

    @commands.command(name='useritems')
    @commands.has_any_role('Technical Commander', 'Republic Droids', 'Commander', 'Economy Lead', 'Economy Admin', 'Art Team')
    @commands.check(is_registered)
    async def useritems(self, ctx, user: discord.Member):
        try:
            user_id = user.id
            purchased_items = get_user_purchases(user_id)  # Ensure this function is defined and works as expected
    
            if purchased_items:
                items_list = "\n".join(purchased_items)
                await ctx.send(f"{user.mention} has purchased the following items:\n{items_list}")
            else:
                await ctx.send(f"{user.mention} has not purchased any items yet.")
        except Exception as e:
            await ctx.send(f"An error occurred while fetching items: {e}")

    @commands.command()
    @commands.has_any_role('Technical Commander', 'Republic Droids', 'Economy Lead', 'Commander')
    async def refund(self, ctx, user: discord.Member, *, item_name: str):
        user_id = user.id
        purchased_items = get_user_purchases(user_id)
    
        if item_name not in purchased_items:
            await ctx.send(f"{user.mention} has not purchased the item '{item_name}'.")
            return
    
        item_price = store_items.get(item_name, 0)
    
        # Remove the item from the user's purchase list
        remove_user_purchase(user_id, item_name)
    
        # Refund the item's price to the user
        current_credits = get_user_credits(user_id, user.roles, role_credits, non_stacking_roles)[0]
        new_credits = current_credits + item_price
        update_user_credits(user_id, new_credits)
    
        await ctx.send(
            f"The item '{item_name}' has been refunded to {user.mention}. {item_price} credits have been returned. New balance: {new_credits} credits.")

async def setup(bot):
    await bot.add_cog(Store(bot))
