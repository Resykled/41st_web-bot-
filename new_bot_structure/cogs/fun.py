import discord
from discord.ext import commands
import asyncio
import random
from utils import *
from database import *

class Fun(commands.Cog):
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
    async def techno(self, ctx):
        await ctx.send(
            "Check this out  https://www.youtube.com/watch?v=Uj1ykZWtPYI&list=PL9JM2aC37BG03vlqyhiYX54NG_thqqvbg ")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def drugs(self, ctx):
        await ctx.send("Deathsticks ?")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def ra(self, ctx):
    
        await ctx.send(
    
            "Check this out  https://tenor.com/view/nigel-farage-up-the-ra-gif-26930624 ")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def kyoda(self, ctx):
        await ctx.send("The requested function took too long to respond and timed out. Please try again later")

    @commands.command()
    async def please(self, ctx, *, request: str = None):
        """Responds politely to any request made with !please"""
        if request:
            responses = [
                f"Of course, {ctx.author.name}! I'll do my best! 😊",
                f"I'm just a bot, but I appreciate the politeness, {ctx.author.name}!",
                f"Thank you for asking nicely, {ctx.author.name}! I'll see what I can do."
            ]
            await ctx.send(random.choice(responses))
        else:
            await ctx.send("Please say what you need help with! 😊")

    @commands.command(name='lean')
    async def lean(self, ctx):
        # Prüfen, ob wir im richtigen Server (Guild) und den richtigen Kanälen sind
        if (ctx.guild and str(ctx.guild.id) == '911409562970628167'
                and ctx.channel.name in ['bot-commands', 'lean-zone']):
    
            gifs = [
                'https://tenor.com/view/the-cup-dave-blunts-blunt-cup-gif-2447846343543578333',
                'https://tenor.com/view/kys-keep-yourself-safe-low-tier-god-gif-24664025',
                'https://tenor.com/view/family-guy-stewie-junkie-stewie-high-stewie-opiates-gif-16490677',
                'https://tenor.com/view/i-love-lean-meme-lean-cat-loves-lean-purple-drank-gif-24893809',
                'https://tenor.com/view/kys-keep-yourself-safe-low-tier-god-gif-24664025',
                'https://tenor.com/view/juice-wrld-juice-wrld-lean-gif-24992173',
                'https://tenor.com/view/lean-minion-i-love-lean-yeah-help-me-love-gif-24941423',
                'https://tenor.com/view/ashe-gif-22268015',
                'https://tenor.com/view/kys-keep-yourself-safe-low-tier-god-gif-24664025',
                'https://tenor.com/view/fate-grand-order-ritsuka-fujimaru-lean-i-love-gif-24868009',
                'https://tenor.com/view/kys-keep-yourself-safe-low-tier-god-gif-24664025',
                'https://tenor.com/view/htp-happy-tree-friends-flippy-flippy-happy-tree-friends-gif-25050180',
                'https://tenor.com/view/i-love-lean-i-love-lean-meme-broly-dragon-ball-super-dragon-ball-super-broly-gif-24908426',
                'https://tenor.com/view/carnage-venom-venom-let-there-be-carnage-lean-carnage-carnage-lean-gif-24709803',
                'https://tenor.com/view/lean-swaggles-swagsoul-funny-i-love-lean-gif-24944891',
                'https://tenor.com/view/i-love-lean-garfield-gif-24997588'
            ]
    
            # Zufälliges GIF auswählen
            random_gif = random.choice(gifs)
    
            # Ausgewähltes GIF senden
            await ctx.send(random_gif)
        else:
            # Falls der Server oder der Channel nicht korrekt ist, kann man hier entweder nichts machen oder eine Meldung senden
            return

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def Sykles(self, ctx):
        await ctx.send("tf are you tring to do here")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def froger(self, ctx):
        # Send the "da frog" message
        await ctx.send("da frog")
    
        # Send the GIF as a separate message
        await ctx.send(
            "https://tenor.com/de/view/frog-jumpscare-jump-jumpscare-frog-toad-jumpscare-gif-17126897754304945804")
    
        print("Sent 'da frog' message and jumpscare GIF link.")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def bitches(self, ctx):
        message = "you have no bitches"
        await ctx.send(message)
        print("no bitches.")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def water(self, ctx):
        message = "Water IS wet https://youtu.be/ugyqOSUlR2A?si=ebf-y4IZtFmpHPpc"
        await ctx.send(message)
        print("water lmao")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def no_you(self, ctx):
        message = "What the fuck did you just fucking say about me, you little bitch? I'll have you know I graduated top of my class in the Navy Seals, and I've been involved in numerous secret raids on Al-Quaeda, and I have over 300 confirmed kills. I am trained in gorilla warfare and I'm the top sniper in the entire US armed forces. You are nothing to me but just another target. I will wipe you the fuck out with precision the likes of which has never been seen before on this Earth, mark my fucking words. You think you can get away with saying that shit to me over the Internet? Think again, fucker. As we speak I am contacting my secret network of spies across the USA and your IP is being traced right now so you better prepare for the storm, maggot. The storm that wipes out the pathetic little thing you call your life. You're fucking dead, kid. I can be anywhere, anytime, and I can kill you in over seven hundred ways, and that's just with my bare hands. Not only am I extensively trained in unarmed combat, but I have access to the entire arsenal of the United States Marine Corps and I will use it to its full extent to wipe your miserable ass off the face of the continent, you little shit. If only you could have known what unholy retribution your little 'clever' comment was about to bring down upon you, maybe you would have held your fucking tongue. But you couldn't, you didn't, and now you're paying the price, you goddamn idiot. I will shit fury all over you and you will drown in it. You're fucking dead, kiddo."
        await ctx.send(message)
        print("no bitches.")

    @commands.command()
    async def FunkyTown(self, ctx):
        # Send the GIF before the lyrics start.
        await ctx.send("https://tenor.com/view/fish-spin-sha-gif-26863370")
    
        # List of lyrics for "Funkytown"
        lyrics = [
            "Gotta make a move to a town that's right for me",
            "Town to keep me movin'",
            "Keep me groovin' with some energy",
            "Well, I talk about it, talk about it",
            "Talk about it, talk about it",
            "Talk about, talk about",
            "Talk about movin'",
            "Gotta move on",
            "Gotta move on",
            "Gotta move on",
            "Won't you take me to",
            "Funkytown?",
            "Won't you take me to",
            "Funkytown?",
            "Won't you take me to",
            "Funkytown?",
            "Won't you take me to",
            "Funkytown?"
        ]
    
        # Loop through each lyric, sending it with a delay and the :speaking_head: emoji at the start.
        for line in lyrics:
            await ctx.send(f":speaking_head: {line}")
            await asyncio.sleep(1)  # Adjust the delay (in seconds) as needed

    @commands.command()
    async def AllStar(self, ctx):
        # Send the GIF before the lyrics start.
        await ctx.send("https://tenor.com/view/shrek-gif-25336944")
    
        # List of lyrics for "Funkytown"
        lyrics = [
           " Somebody once told me",
           " The world is gonna roll me",
            "I ain't the sharpest tool in the shed",
            "She was looking kind of dumb",
            "With her finger and her thumb",
            "In the shape of an L on her forehead",
            "Well, the years start coming",
            "And they don't stop coming",
            "Fed to the rules and I hit the ground running",
            "Didn't make sense not to live for fun",
            "Your brain gets smart, but your head gets dumb",
            "So much to do, so much to see",
            "So what's wrong with taking the back streets?",
            "You'll never know if you don't go",
            "You'll never shine if you don't glow",
            "Hey now, you're an all star",
            "Get your game on, go play",
            "Hey now, you're a rock star",
            "Get the show on, get paid",
            "And all that glitters is gold",
            "Only shooting stars"
    
        
        ]
    
        # Loop through each lyric, sending it with a delay and the :speaking_head: emoji at the start.
        for line in lyrics:
            await ctx.send(f":speaking_head: {line}")
            await asyncio.sleep(1)  # Adjust the delay (in seconds) as needed

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def monte(self, ctx):
        user_id = "1047317588755095592"  # Replace with the actual user ID of "monte"
        user = await self.bot.fetch_user(user_id)
        if user:
            await ctx.send(f" touch grass, {user.mention}!")
            print(f"Sent touch crazy message and pinged {user.display_name} ({user_id}).")
        else:
            await ctx.send("Could not find the user monte.")
            print("Could not find the user monte.")

    @commands.command(name='rps')
    @is_allowed_channel()
    @commands.check(is_registered)
    async def rock_paper_scissors(self, ctx, user_choice: str):
        choices = ['rock', 'paper', 'scissors']
        bot_choice = random.choice(choices)
    
        if user_choice.lower() not in choices:
            await ctx.send(f"Invalid choice! Please choose rock, paper, or scissors.")
            return
    
        if user_choice.lower() == bot_choice:
            result = "It's a tie!"
        elif (user_choice.lower() == 'rock' and bot_choice == 'scissors') or \
                (user_choice.lower() == 'scissors' and bot_choice == 'paper') or \
                (user_choice.lower() == 'paper' and bot_choice == 'rock'):
            result = "You win!"
        else:
            result = "You lose!"
    
        await ctx.send(f'You chose {user_choice}, I chose {bot_choice}. {result}')

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def gravestone(self, ctx):
        user_id = "814590259219660831"  # Gravestone ID
        user = await self.bot.fetch_user(user_id)
        if user.id == int(user_id):
            await ctx.send("{user.mention}, you should fix this.")
        else:
            await ctx.send(f"Hey, {user.mention}, come make sure everything works!")

    @commands.command()
    @is_allowed_channel()
    @commands.check(is_registered)
    async def nuke(self, ctx):
    	user_id = "690011602510282771"  # Nuke ID
    	gravestone_id = "814590259219660831"
    	user = await self.bot.fetch_user(user_id)
    	if user.id == int(user_id):
    		await ctx.send(f"Hows it going, {user.mention}?")
    	elif user.id == int(gravestone_id):
    		await ctx.send(f"Hey, {user.mention}, not your command,you aint nuclear!")
    	else:
    		await ctx.send("Not for you")

async def setup(bot):
    await bot.add_cog(Fun(bot))
