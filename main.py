import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime

# Import our db helper functions
import db

# Initialize or ensure DB is set up:
db.init_db()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix='$', intents=intents)

# ------------------------------------------
# --- NEW OR CHANGED ---
# Channel IDs (update with actual channel IDs):
CAMP_MAP_ID = 1358095717469786325
CAMP_ANNOUNCE_ID = 1358095473520672949
CAMP_LOGS_ID = 1358095616630194277
CAMP_COMMANDS_ID = 1358095801590743060
CAMP_STATUS_ID = 1349129302972694618
# ------------------------------------------
campaign_status_message_id = None
# In-memory structure for voting
voting_session_active = False
current_vote = {"north": 0, "south": 0, "east": 0, "west": 0}
vote_message_id = None
vote_start_time = None
vote_duration = 12 * 3600  # 12 hours in seconds

# Movement helper
MOVES = {
    "north": (0, -1),  # y - 1
    "south": (0, 1),  # y + 1
    "east": (1, 0),  # x + 1
    "west": (-1, 0),  # x - 1
}

WIN_ANNOUNCEMENTS = [
    "**Good work troopers! With that objective achieved we've made a significant breakthrough on liberating this planet...**",
    "**Excellent shooting men! With the enemy defeated for now, we can continue our advance...**",
    "**Fleet reports enemy signatures dropping, whoever's left is on the run...**",
    "**Excellent work men! We're one step closer to taking this planet for the Republic...**",
    "**Look at those seppies run! Troopers, rally together and lets demolish the rest of them...**",
    "**Air support is on the way to help with clean-up, late as usual to the party!...**",
    "**That did it troopers! The clankers are in a full-scale retreat...**",
    "**Word has it that Republic Commandos were able to break through...**",
    "**Get heavy weapons set up troopers! We've won the day, but those droids are absolutely going to be working their way back...**",
    "**Heavy armor is obliterating the last of the enemy forces as they attempt to make their escape...**"
]

LOSS_ANNOUNCEMENTS = [
    "**Pack it up men, we've lost too many brothers to continue the offensive...**",
    "**We did what we could troopers, but the Seppies have us beat this time...**",
    "**Heads down! Our vanguard just got blasted and now they're coming for us...**",
    "**Mission failed men, we couldn't crack the droids. They're using this as an opportunity to push us hard...**",
    "**Buckle up troopers, we're in for the fight of our lives now...**",
    "**Take cover men! Venators in orbit are providing an orbital bombardment for us to make our retreat...**",
    "**Commando droids just took out our left flank and are about to make contact!**",
    "**Those droidekas have tough shields! They're counterpushing with those rollers...**",
    "**Those supers have tough armor! They're breaking through our forward positions...**",
    "**That's it men, we've lost too many troopers to continue the push...**",
]

# Define positive and negative rule lists
positive_rules = {
    "CLASS": [
        "**Assault Only** \n + 1 reinforcement class\n",
        "**Assault Only**  \n + allowing heroes\n",
        "**Heavy Only** \n + 1 reinforcement class\n",
        "**Heavy Only**  \n + allowing heroes\n",
        "**Specialist Only**  \n + 1 reinforcement class\n",
        "**Specialist Only**  \n + allowing heroes\n",
        "**Officer only**  \n + 1 reinforcement class\n",
        "**Officer only**  \n + allowing heroes\n"
    ],
    "WEAPON": [
        "**Up in their face** \n (ASSAULT: CR-2, E-11D; HEAVY: TL-50; SPECIALIST: A-280CFE; OFFICER: Blurrg, SE-44C)\n",
        "**Long Distance** \n (ASSAULT: EL-16HFE; HEAVY: T-21; SPECIALIST: NT-242; OFFICER: S-5)\n"
    ],
    "STAR_CARD": [
        "**ASSAULT:** \n Carabiners (Improved Weapons Handling, Bodyguard, Grenade of choice)\n",
        "**ASSAULT:** \n Close and Personal (Assault Training, Bodyguard, Toughen up)\n",
        "**HEAVY:** \n We go Boom (Improved Grenade/detonite charge, Barrage, Explosive Sentry)\n",
        "**HEAVY:** \n Brawlers (ICS, Detonite Charge, Bodyguard)\n",

        "**HEAVY** \n + one base class only (HEAVY: Turtles - ICS, Bodyguard, Survivalist)\n",
        "**SPECIALIST:** \n Wack-a-mole (Stealth, Hardened Infiltration, Personal Shield)\n",
        "**SPECIALIST:** \n Snipers (Marksman, Trip Mine, Stealth)\n",
        "**SPECIALIST:** \n Tooth and Nail (Improved Shock, Killstreak Infil, Survivalist)\n",
        "**OFFICER:** \n Commanders (Improved Battle Command, Blaster Turret, Officer’s Presence)\n",
        "**OFFICER:** \n Missile Operator (Recharge Command, Homing Shot, Resourceful)\n"
    ]
}

negative_rules = {
    "CLASS": [
        "**Assault Only** \n + use EL-16HF\n",
        "**Heavy Only** \n + use FWMBK\n",
        "**Specialist Only** \n + use Cycler Rifle\n",
        "**Officer only** \n + use BLURRG-1120\n"
    ],
    "WEAPON": [
        "**Medium Engagement** \n (ASSAULT: A280/default; HEAVY: DC-15, DC-15LE, FWMB-10K; SPECIALIST: VALKEN, IQA, CYCLER; OFFICER: Default, DL-18)\n"
    ],
    "STAR_CARD": [
        "**No Star Cards!**",
        "**No Star Cards** \n + Base Classes Only\n",
        "**No Star Cards** \n + one base class only (ASSAULT: Memesault - Flash pistol, Slug Vanguard, Acid Launcher)\n",
        "**No Star Cards** \n + one base class only (ASSAULT: Distantly Deadly - Marksman, Improved Scan Dart, Acid/Improved/Ion Grenades)\n",
        "**No Star Cards** \n + one base class only (HEAVY: Defenders - Expert Weapons Handling, ICS, Mobile Sentry/Supercharged Sentry)\n",
        "**No Star Cards** \n + one base class only (SPECIALIST: Scouts - Scramble, Improved Binos, Repulsor Cannon)\n",
        "**No Star Cards** \n + one base class only (SPECIALIST: Stingers - Stinger Pistol, other star cards)\n",
        "**No Star Cards** \n + one base class only (OFFICER: Phalanx - Recharge Command, Squad Shield, Defuser)\n",
        "**No Star Cards** \n + one base class only (OFFICER: Urban Specialist - Survivalist, Disruption, Blast Command)\n"
    ]
}
def is_Technical_Commander():
    async def predicate(ctx):
        bot_dev_role = discord.utils.get(ctx.guild.roles, name="Technical Commander, Commander")
        if bot_dev_role in ctx.author.roles:
            return True
        await ctx.send("You do not have permission to use this command.")
        return False

    return commands.check(predicate)


def Right_role():
    async def predicate(ctx):
        allowed_roles = [
            "Technical Commander",
            "Corporal",
            "Sergeant",
            "Staff Sergeant",
            "Sergeant Major",
            "2nd Lieutenant",
            "Lieutenant",
            "Captain",
            "Major",
            "Commander"
        ]
        if any(role.name in allowed_roles for role in ctx.author.roles):
            return True
        await ctx.send("You do not have permission to use this command.")
        return False

    return commands.check(predicate)



# --- NEW OR CHANGED ---
# Global check: all commands except raid_win / raid_loss must be called in campain-commands channel

@bot.check
def global_channel_check(ctx):
    if ctx.command.name in ("raid_win", "raid_loss", "map"):
        # These two commands must be in campain-logs, so skip the global check here
        return True
    return ctx.channel.id == CAMP_COMMANDS_ID


# ------------------------

@tasks.loop(minutes=1)
async def campaign_status_update():
    """
    Updates the campaign status message in the designated status channel.
    The message includes:
      - The current map (using render_friendly_map) plus a legend.
      - Active special rule details (if one is active): rule type, rule text,
        remaining raid count, and time remaining.
      - Current voting session info: vote counts per direction and time remaining.
      - HQ objectives counts: how many friendly and enemy HQs remain.
    It ensures that the channel contains only one message.
    """
    global campaign_status_message_id
    channel = bot.get_channel(CAMP_STATUS_ID)
    if channel is None:
        print("[DEBUG] Campaign status channel not found.")
        return

    # Retrieve the current game state
    state = db.get_game_state()

    # 1. Build the map and legend section.
    map_str = render_friendly_map(state)
    legend = (
        "Legend:\n"
        "⬜ - Hidden\n"
        "⬛ - Visited / Old HQ\n"
        "🟩 - Friendly HQ\n"
        "🟥 - Enemy HQ\n"
        "🟦 - Friendly Marker\n"
        "🟪 - Enemy Marker\n"
        "🟨 - Side Quest"
    )
    map_section = f"**Campaign Map:**\n```\n{map_str}\n```\n{legend}"

    # 2. Active special rule info.
    active_rule = state.get("active_rule", {})
    if active_rule.get("rule"):
        try:
            expires_at = datetime.datetime.fromisoformat(active_rule["expires_at"])
            time_remaining = expires_at - datetime.datetime.utcnow()
            time_remaining_str = str(time_remaining).split('.')[0] if time_remaining.total_seconds() > 0 else "Expired"
        except Exception as e:
            print(f"[DEBUG] Error parsing active rule expiry: {e}")
            time_remaining_str = "Unknown"
        rule_section = (
            f"**Active Special Rule:** {active_rule['type'].title()} - **{active_rule['rule']}**\n"
            f"Raids remaining: {active_rule['raid_count']}\n"
            f"Time remaining: {time_remaining_str}"
        )
    else:
        rule_section = "**Active Special Rule:** None"

    # 3. Voting session info.
    if voting_session_active:
        vote_section = "**Voting Session:** Active\n"
        for direction, count in current_vote.items():
            vote_section += f"{direction.title()}: {count} votes\n"
        if vote_start_time:
            now = datetime.datetime.utcnow()
            elapsed = (now - vote_start_time).total_seconds()
            remaining = vote_duration - elapsed
            if remaining > 0:
                hrs, rem = divmod(remaining, 3600)
                mins, secs = divmod(rem, 60)
                vote_section += f"Time remaining: {int(hrs)}h {int(mins)}m {int(secs)}s"
            else:
                vote_section += "Voting session ending soon"
    else:
        vote_section = "**Voting Session:** Not active"

    # 4. HQ Objectives info.
    grid = state["grid"]
    friendly_count = sum(cell["state"] == "friendly_objective" for row in grid for cell in row)
    enemy_count = sum(cell["state"] == "enemy_objective" for row in grid for cell in row)
    hq_section = f"**HQ Objectives:**\nFriendly: {friendly_count}\nEnemy: {enemy_count}"

    # Combine all sections into one status message.
    status_message = "\n\n".join([map_section, rule_section, vote_section, hq_section])

    # Delete any existing messages in this channel except the one we're updating.
    try:
        messages = [msg async for msg in channel.history(limit=100)]
        for msg in messages:
            if campaign_status_message_id and msg.id == campaign_status_message_id:
                continue
            try:
                await msg.delete()
            except Exception as e:
                print(f"[DEBUG] Error deleting message: {e}")
    except Exception as e:
        print(f"[DEBUG] Error fetching channel history: {e}")

    # Update the existing status message or send a new one.
    if campaign_status_message_id:
        try:
            msg = await channel.fetch_message(campaign_status_message_id)
            await msg.edit(content=status_message)
        except Exception as e:
            print(f"[DEBUG] Error editing status message: {e}. Sending new message.")
            new_msg = await channel.send(status_message)
            campaign_status_message_id = new_msg.id
    else:
        new_msg = await channel.send(status_message)
        campaign_status_message_id = new_msg.id



@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    # Optionally, start background tasks
    daily_event_check.start()
    vote_check_loop.start()
    hq_event_check_loop.start()
    campaign_status_update.start()


def can_move_back(last_direction, new_direction):
    opposites = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }
    return opposites.get(last_direction) == new_direction


def get_opposite_direction(direction: str) -> str:
    opposites = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }
    return opposites.get(direction, "")


def find_nearest_friendly_hq(state):
    enemy_x, enemy_y = state["enemy_x"], state["enemy_y"]
    friendly_hqs = []

    for x in range(10):
        for y in range(10):
            if state["grid"][x][y]["state"] == "friendly_objective":
                friendly_hqs.append((x, y))

    if not friendly_hqs:
        return None

    # Manhattan distance
    nearest_hq = min(
        friendly_hqs,
        key=lambda hq: abs(enemy_x - hq[0]) + abs(enemy_y - hq[1])
    )
    return nearest_hq


def move_enemy_toward_hq(state):
    """
    Moves the enemy one step (cardinal only) toward the nearest friendly HQ.
    It chooses a move (north, south, east, or west) that reduces the Manhattan distance.
    """
    nearest_hq = find_nearest_friendly_hq(state)
    if not nearest_hq:
        print("[DEBUG] move_enemy_toward_hq: No friendly HQ found.")
        return state  # No friendly HQ found

    target_x, target_y = nearest_hq
    enemy_x, enemy_y = state["enemy_x"], state["enemy_y"]
    current_distance = abs(enemy_x - target_x) + abs(enemy_y - target_y)

    # Define the four cardinal moves.
    directions = {
        "north": (0, -1),
        "south": (0, 1),
        "east": (1, 0),
        "west": (-1, 0)
    }

    possible_moves = []
    for d, (dx, dy) in directions.items():
        cand_x = enemy_x + dx
        cand_y = enemy_y + dy
        # Ensure the move is within bounds.
        if 0 <= cand_x < 10 and 0 <= cand_y < 10:
            new_distance = abs(cand_x - target_x) + abs(cand_y - target_y)
            if new_distance < current_distance:
                possible_moves.append((d, cand_x, cand_y))

    if not possible_moves:
        print(
            "[DEBUG] move_enemy_toward_hq: No cardinal move reduces distance; enemy stays at ({}, {}).".format(enemy_x,
                                                                                                               enemy_y))
        return state  # Enemy can't move closer by a cardinal move.

    # Choose one move among the possible ones (randomly for variation).
    chosen_direction, new_x, new_y = random.choice(possible_moves)
    print(
        f"[DEBUG] move_enemy_toward_hq: Enemy moving from ({enemy_x}, {enemy_y}) to ({new_x}, {new_y}) using '{chosen_direction}' toward friendly HQ at ({target_x}, {target_y}).")

    state["enemy_x"] = new_x
    state["enemy_y"] = new_y
    return state


def reposition_enemy_hq(grid, old_x, old_y):
    """
    Entfernt das Enemy-HQ von (old_x, old_y) und
    setzt es an eine zufällige neue Position auf der Karte,
    die kein Friendly-HQ und kein Enemy-HQ ist.
    """
    grid[old_x][old_y]["state"] = "visited"


    possible_cells = []
    for x in range(10):
        for y in range(10):
            if grid[x][y]["state"] not in ["friendly_objective", "enemy_objective"]:
                possible_cells.append((x, y))


    if not possible_cells:
        return (old_x, old_y)

    # Zufällige neue Position wählen
    new_x, new_y = random.choice(possible_cells)
    grid[new_x][new_y]["state"] = "enemy_objective"
    return (new_x, new_y)


def reposition_friendly_hq(grid, old_x, old_y):
    """
    Removes the attacked friendly HQ from (old_x, old_y) by marking it as visited,
    then places a new friendly HQ in a random cell that is not already an HQ.
    """
    # Remove the old HQ.
    grid[old_x][old_y]["state"] = "visited"

    # Gather all cells that are NOT already designated as any HQ.
    possible_cells = []
    for x in range(10):
        for y in range(10):
            if grid[x][y]["state"] not in ["friendly_objective", "enemy_objective"]:
                possible_cells.append((x, y))

    # If no cell is available, return the original coordinates.
    if not possible_cells:
        return (old_x, old_y)

    # Choose a new cell at random and mark it as the friendly HQ.
    new_x, new_y = random.choice(possible_cells)
    grid[new_x][new_y]["state"] = "friendly_objective"
    return (new_x, new_y)



@tasks.loop(minutes=1)
async def enemy_movement_loop():
    state = db.get_game_state()

    # Move the enemy
    state = move_enemy_toward_hq(state)
    db.update_game_state(state)

    # --- NEW OR CHANGED ---
    # Post updated map to campaign-map
    map_channel = bot.get_channel(CAMP_MAP_ID)
    updated_map = render_friendly_map(state)
    await map_channel.send("**Map updated after enemy movement!**\n```\n" + updated_map + "\n```")
    # ----------------------

    await check_if_enemy_on_friendly_hq(state)


async def check_if_enemy_on_friendly_hq(state):
    ex, ey = state["enemy_x"], state["enemy_y"]
    if 0 <= ex < 10 and 0 <= ey < 10:
        cell_state = state["grid"][ex][ey]["state"]
        if cell_state == "friendly_objective":
            # Defense event triggered
            # --- CHANGED channel from old ID to announcements
            channel = bot.get_channel(CAMP_ANNOUNCE_ID)
            if channel:
                await channel.send("Friendly HQ under attack! We have 5 hours to defend it!")
            start_hq_event(state, "defense", ex, ey)


async def check_if_friendly_on_enemy_hq(state):
    fx, fy = state["friendly_x"], state["friendly_y"]
    if 0 <= fx < 10 and 0 <= fy < 10:
        cell_state = state["grid"][fx][fy]["state"]
        if cell_state == "enemy_objective":
            channel = bot.get_channel(CAMP_ANNOUNCE_ID)
            if channel:
                await channel.send("We are attacking an enemy HQ! We got 5h till reinforcements arrive!")
            start_hq_event(state, "attack", fx, fy)


def start_hq_event(state, event_type, target_x, target_y):
    now = datetime.datetime.utcnow()
    end_time = now + datetime.timedelta(hours=5)

    hq_event = {
        "active": True,
        "type": event_type,
        "start_time": now.isoformat(),
        "end_time": end_time.isoformat(),
        "wins_required": 6 if event_type == "defense" else 8,
        "wins": 0,
        "target_x": target_x,
        "target_y": target_y
    }

    state["hq_event"] = hq_event
    db.update_game_state(state)
    print(
        f"[DEBUG] start_hq_event: Starting {event_type} event at ({target_x}, {target_y}). Wins required: {hq_event['wins_required']}. Event will end at {hq_event['end_time']}.")


def get_random_buff():
    # Combine all positive rules into one list and return a random choice.
    all_buffs = positive_rules["CLASS"] + positive_rules["WEAPON"] + positive_rules["STAR_CARD"]
    return random.choice(all_buffs)

def get_random_nerfs():
    # For punishment, pick one random rule from each negative category.
    nerf_list = []
    for cat in ["CLASS", "WEAPON", "STAR_CARD"]:
        nerf_list.append(random.choice(negative_rules[cat]))
    return nerf_list

# Special cells (side objectives) data: 5 fixed special rule sets.
special_cells_data = [
    {"type": "buff", "rule": "Everyone Plays RC / B2"},
    {"type": "nerf", "rule": "Everyone Plays Cycler rifle"},
    {"type": "nerf", "rule": "Everyone Plays FWMBK"},
    {"type": "buff", "rule": "One Person Plays an hero of choice"},
    {"type": "nerf", "rule": "IQE Without star Cards"}
]

def place_special_cells(grid):
    """
    Randomly select 5 hidden cells to become buff/nerf cells.
    The cell state is set to "buff_nerf" and its special rule details are attached.
    """
    hidden_cells = [(x, y) for x in range(10) for y in range(10) if grid[x][y]["state"] == "hidden"]
    random.shuffle(hidden_cells)
    for cell_rule in special_cells_data:
        if hidden_cells:
            x, y = hidden_cells.pop()
            grid[x][y]["state"] = "buff_nerf"
            grid[x][y]["special_rule_type"] = cell_rule["type"]
            grid[x][y]["special_rule_description"] = cell_rule["rule"]
    return grid

def check_special_cell(state, x, y, ctx=None):
    """
    Checks if the cell at (x, y) is a special side quest cell (buff/nerf).
    If so, it adds the corresponding rule to the rule register, updates the cell state to "visited",
    and announces the collection in the current context (or in the announcement channel).
    """
    cell = state["grid"][x][y]
    if cell["state"] == "buff_nerf":
        rule_type = cell.get("special_rule_type")
        rule_desc = cell.get("special_rule_description")
        # Ensure the rule register exists
        if "rule_register" not in state:
            state["rule_register"] = {"buffs": [], "nerfs": []}
        if rule_type == "buff":
            state["rule_register"]["buffs"].append(rule_desc)
        elif rule_type == "nerf":
            state["rule_register"]["nerfs"].append(rule_desc)
        # Mark the cell as visited so it can't be collected again
        cell["state"] = "visited"
        announcement = f"Friendly troops have collected a special {rule_type}: **{rule_desc}**!"
        db.update_game_state(state)
        if ctx:
            # Send announcement using the provided context
            asyncio.create_task(ctx.send(announcement))
        else:
            # If no context is available, use the announcements channel
            channel = bot.get_channel(CAMP_ANNOUNCE_ID)
            if channel:
                asyncio.create_task(channel.send(announcement))
        return rule_type, rule_desc
    return None, None



async def finish_hq_event(state, success):
    hq_event = state["hq_event"]
    grid = state["grid"]

    print(f"[DEBUG] finish_hq_event: Ending HQ event of type {hq_event['type']} with success = {success}.")

    if success:
        if hq_event["type"] == "attack":
            grid[hq_event["target_x"]][hq_event["target_y"]]["state"] = "friendly_objective"
            buff_reward = get_random_buff()
            state["rule_register"]["buffs"].append(buff_reward)
            announcement = f"**Attack SUCCESS!** \n `Enemy HQ captured! Reward gained:` **{buff_reward}**"
            print(f"[DEBUG] finish_hq_event: Buff reward assigned: {buff_reward}")
        else:
            # Defense event: reposition the friendly HQ.
            old_x = hq_event["target_x"]
            old_y = hq_event["target_y"]
            new_x, new_y = reposition_friendly_hq(grid, old_x, old_y)
            announcement = f"**Defense SUCCESS!** \n `Friendly HQ repositioned to` ({new_x}, {new_y})!"
    else:
        if hq_event["type"] == "defense":
            grid[hq_event["target_x"]][hq_event["target_y"]]["state"] = "visited"
            nerf_rewards = get_random_nerfs()
            state["rule_register"]["nerfs"].extend(nerf_rewards)
            announcement = f"**Defense FAILED!** \n `HQ lost. Punishments applied:` {' '.join(nerf_rewards)}"
            print(f"[DEBUG] finish_hq_event: Nerf punishments assigned: {nerf_rewards}")
        else:
            old_x = hq_event["target_x"]
            old_y = hq_event["target_y"]
            reposition_enemy_hq(grid, old_x, old_y)
            announcement = "**Attack FAILED!** \n `Enemy repositioned!`"

    # Announce the outcome and update state...
    channel = bot.get_channel(CAMP_ANNOUNCE_ID)
    if channel:
        text_snippet = random.choice(WIN_ANNOUNCEMENTS) if success else random.choice(LOSS_ANNOUNCEMENTS)
        await channel.send(f"{announcement}\n{text_snippet}")
    else:
        print("[DEBUG] finish_hq_event: CAMP_ANNOUNCE_ID channel not found.")

    # Reset HQ event data.
    state["hq_event"] = {
        "active": False,
        "type": "",
        "start_time": "",
        "end_time": "",
        "wins_required": 0,
        "wins": 0,
        "losses": 0,
        "target_x": -1,
        "target_y": -1
    }
    print("[DEBUG] finish_hq_event: HQ event data reset. active=False")
    db.update_game_state(state)

    map_channel = bot.get_channel(CAMP_MAP_ID)
    if map_channel:
        updated_map = render_friendly_map(state)
        await map_channel.send("**Map updated after HQ event!**\n```\n" + updated_map + "\n```")
    else:
        print("[DEBUG] finish_hq_event: CAMP_MAP_ID channel not found.")

    await check_campaign_status(state)


@bot.command(name="berfs")
async def list_berfs(ctx):
    """
    Lists all currently stockpiled raid effects.
    """
    state = db.get_game_state()
    register = state.get("rule_register", {"buffs": [], "nerfs": []})
    buff_list = register.get("buffs", [])
    nerf_list = register.get("nerfs", [])
    msg = "**Positive Raid Rules:**\n"
    if buff_list:
        for idx, rule in enumerate(buff_list, start=1):
            msg += f"Rule Set {idx}: {rule}\n"
    else:
        msg += "None\n"
    msg += "\n**Negative Raid Rules:**\n"
    if nerf_list:
        for idx, rule in enumerate(nerf_list, start=1):
            msg += f"Rule Set {idx}: {rule}\n"
    else:
        msg += "None\n"
    await ctx.send(msg)

@bot.command(name="srule")
@Right_role()
async def select_rule(ctx):
    """
    Allows a user to activate a stockpiled rule set.
    Negative rules are prioritized if available.
    The activated rule remains for 3 raid results or 2 hours.
    """
    state = db.get_game_state()
    active = state.get("active_rule", {})
    if active.get("rule"):
        await ctx.send("A special rule is already active.")
        return

    register = state.get("rule_register", {"buffs": [], "nerfs": []})
    chosen_rule = None
    rule_type = None
    # Prioritize negative rules if available
    if register.get("nerfs"):
        chosen_rule = register["nerfs"].pop(0)
        rule_type = "nerf"
    elif register.get("buffs"):
        chosen_rule = register["buffs"].pop(0)
        rule_type = "buff"
    else:
        await ctx.send("No special rules available in the register.")
        return

    now = datetime.datetime.utcnow()
    active_rule = {
        "rule": chosen_rule,
        "type": rule_type,
        "activated_by": ctx.author.id,
        "activated_at": now.isoformat(),
        "raid_count": 3,  # active for next 3 raids
        "expires_at": (now + datetime.timedelta(hours=2)).isoformat()
    }
    state["active_rule"] = active_rule
    db.update_game_state(state)
    await ctx.send(f"Special {rule_type} rule activated: **{chosen_rule}**. It will expire after 3 raids or 2 hours, whichever comes first.")

@bot.command(name="aberfs")
async def active_berfs(ctx):
    """
    Displays the currently active special rule set.
    """
    state = db.get_game_state()
    active = state.get("active_rule", {})
    if active.get("rule"):
        expires_at = datetime.datetime.fromisoformat(active["expires_at"])
        time_left = expires_at - datetime.datetime.utcnow()
        await ctx.send(
            f"Active Special Rule ({active['type']}): **{active['rule']}**\n"
            f"Raids remaining: {active['raid_count']}\n"
            f"Time remaining: {str(time_left).split('.')[0]}"
        )
    else:
        await ctx.send("No special rule is currently active.")

# --- Background Task: Check active rule expiration ---
@tasks.loop(minutes=1)
async def active_rule_expiration_check():
    state = db.get_game_state()
    active = state.get("active_rule", {})
    if active.get("rule"):
        expires_at = datetime.datetime.fromisoformat(active["expires_at"])
        if datetime.datetime.utcnow() >= expires_at:
            try:
                user = await bot.fetch_user(active["activated_by"])
            except Exception as e:
                print(f"[DEBUG] Error fetching user: {e}")
                user = None
            channel = bot.get_channel(CAMP_ANNOUNCE_ID)
            if channel and user:
                await channel.send(f"{user.mention}, your special rule **{active['rule']}** has expired due to time limit.")
            state["active_rule"] = {}
            db.update_game_state(state)


def single_step_move(x, y, direction):
    dx, dy = MOVES.get(direction, (0, 0))

    new_x = x + dx
    new_y = y + dy

    # Auf [0..9] begrenzen
    new_x = max(0, min(9, new_x))
    new_y = max(0, min(9, new_y))

    return new_x, new_y


@tasks.loop(seconds=30)
async def vote_check_loop():
    global voting_session_active, current_vote, vote_message_id, vote_start_time

    if voting_session_active and vote_start_time:
        now = datetime.datetime.utcnow()
        elapsed = (now - vote_start_time).total_seconds()
        if elapsed >= vote_duration:
            voting_session_active = False

            sorted_votes = sorted(current_vote.items(), key=lambda x: x[1], reverse=True)
            winner_direction, winner_count = sorted_votes[0]

            state = db.get_game_state()
            last_dir = state["last_move_direction"]

            old_x, old_y = state["friendly_x"], state["friendly_y"]

            if can_move_back(last_dir, winner_direction):
                if len(sorted_votes) > 1 and sorted_votes[1][1] > 0:
                    winner_direction = sorted_votes[1][0]
                    winner_count = sorted_votes[1][1]

            new_x, new_y = single_step_move(old_x, old_y, winner_direction)
            state["friendly_x"] = new_x
            state["friendly_y"] = new_y
            state["last_move_direction"] = winner_direction

            if state["grid"][new_x][new_y]["state"] == "hidden":
                state["grid"][new_x][new_y]["state"] = "visited"

            db.update_game_state(state)
            check_special_cell(state, new_x, new_y, None)

            # >>> NEU: Check, ob Friendly auf Enemy-HQ steht <<<
            await check_if_friendly_on_enemy_hq(state)

            print(f"[DEBUG] vote_check_loop: from ({old_x},{old_y}) -> ({new_x},{new_y}) via '{winner_direction}'")

            # Ergebnis ansagen
            channel = bot.get_channel(CAMP_ANNOUNCE_ID)
            if channel:
                await channel.send(
                    f"Voting ended! The winning direction was **{winner_direction.upper()}** "
                    f"with {winner_count} votes. Friendly position moved to ({new_x}, {new_y})."
                )

            # Karte posten
            map_channel = bot.get_channel(CAMP_MAP_ID)
            updated_map = render_friendly_map(state)
            await map_channel.send("**Map updated after the vote!**\n```\n" + updated_map + "\n```")

            # Voting-Daten zurücksetzen
            current_vote = {}
            vote_message_id = None
            vote_start_time = None


@tasks.loop(hours=24)
async def daily_event_check():
    state = db.get_game_state()
    if not state["special_event_active"]:
        if random.choice([True, False]):  # 50% chance
            state["special_event_active"] = True
            state["special_event_end_time"] = (datetime.datetime.utcnow() + datetime.timedelta(hours=5)).isoformat()
            state["event_name"] = "Daily Double Progress!"
            db.update_game_state(state)

            # --- CHANGED to announcements channel
            channel = bot.get_channel(1338952435921584138)
            if channel:
                await channel.send("A special event has started! Double progress for the next 5 hours!")
    else:
        end_time = datetime.datetime.fromisoformat(state["special_event_end_time"])
        if datetime.datetime.utcnow() >= end_time:
            state["special_event_active"] = False
            state["event_name"] = ""
            state["special_event_end_time"] = ""
            db.update_game_state(state)

            channel = bot.get_channel(CAMP_ANNOUNCE_ID)
            if channel:
                await channel.send("The special event has ended!")


@tasks.loop(minutes=1)
async def hq_event_check_loop():
    state = db.get_game_state()
    hq_event = state.get("hq_event", {})
    if not hq_event.get("active"):
        return

    end_time_str = hq_event.get("end_time", "")
    if not end_time_str:
        return

    now = datetime.datetime.utcnow()
    end_time = datetime.datetime.fromisoformat(end_time_str)
    remaining_time = end_time - now
    wins = hq_event.get("wins", 0)
    losses = hq_event.get("losses", 0)
    print(
        f"[DEBUG] hq_event_check_loop: Time remaining for HQ event: {remaining_time}. Wins: {wins}, Losses: {losses}.")

    if now >= end_time:
        required = hq_event["wins_required"]
        current = hq_event["wins"]
        success = (current >= required)
        await finish_hq_event(state, success)


def move_and_mark_visited(state, direction):
    if direction not in MOVES:
        direction = "north"

    new_x, new_y = single_step_move(state["friendly_x"], state["friendly_y"], direction)
    state["friendly_x"] = new_x
    state["friendly_y"] = new_y

    if state["grid"][new_x][new_y]["state"] == "hidden":
        state["grid"][new_x][new_y]["state"] = "visited"

    state["last_move_direction"] = direction
    return state


def move_enemy_after_losses(state):
    """
    When 10 losses are reached, move the enemy toward the nearest friendly HQ using
    a cardinal move only, then reset the loss counter.
    """
    print(f"[DEBUG] move_enemy_after_losses: Losses reached {state['losses']}. Initiating enemy move.")
    state = move_enemy_toward_hq(state)
    state["losses"] = 0
    print(
        f"[DEBUG] move_enemy_after_losses: Enemy moved to ({state['enemy_x']}, {state['enemy_y']}). Loss counter reset.")
    return state


async def handle_raid_result(ctx, result):
    state = db.get_game_state()
    hq_event = state.get("hq_event", {})

    # 1) HQ-Event in progress?
    if hq_event.get("active"):
        if result == "win":
            hq_event["wins"] += 1
            db.update_game_state(state)
            current = hq_event["wins"]
            req = hq_event["wins_required"]
            print(f"[DEBUG] handle_raid_result: HQ event win registered. Current wins: {current}/{req}.")
            await ctx.send(f"HQ-Event: +1 win ({current}/{req})")
            if current >= req:
                await finish_hq_event(state, True)
        else:
            hq_event["losses"] = hq_event.get("losses", 0) + 1
            print(f"[DEBUG] handle_raid_result: HQ event loss registered. Current losses: {hq_event['losses']}.")
            if hq_event["losses"] >= 4:
                await ctx.send("HQ-Event: Too many losses! We have failed to defend/attack in time!")
                await finish_hq_event(state, False)
            else:
                await ctx.send(f"HQ-Event: Loss registered. Total losses: {hq_event['losses']}. Keep pushing troopers!")
            db.update_game_state(state)
        return

    # 2) Standard raid logic when no HQ-Event is active:
    if result == "win":
        increment = 2 if state["special_event_active"] else 1
        state["wins"] += increment
        if state["wins"] >= 10:
            state["wins"] -= 10
            await ctx.send("10 wins reached! Starting a voting session and resetting the win counter...")
            announce_ch = bot.get_channel(CAMP_ANNOUNCE_ID)
            await start_voting(announce_ch)
        else:
            await ctx.send(f"Raid won! Total wins: {state['wins']}")
    else:
        increment = 2 if state["special_event_active"] else 1
        state["losses"] += increment
        print(f"[DEBUG] handle_raid_result: Raid lost. Losses incremented to {state['losses']}.")
        if state["losses"] >= 5 :
            state = move_enemy_after_losses(state)
            print("[DEBUG] handle_raid_result: Enemy moved due to reaching 10 losses.")
            await ctx.send("Enemy moved due to reaching 10 losses.")
            map_channel = bot.get_channel(CAMP_MAP_ID)
            if map_channel:
                updated_map = render_friendly_map(state)
                await map_channel.send("**Map updated after enemy movement!**\n```\n" + updated_map + "\n```")
            else:
                print("[DEBUG] handle_raid_result: Map channel not found.")
            await check_if_enemy_on_friendly_hq(state)
        else:
            await ctx.send(f"Raid lost! Total losses: {state['losses']}")

    # Decrement the active rule's raid counter (if one is active)
    if state.get("active_rule", {}).get("rule"):
        state["active_rule"]["raid_count"] -= 1
        print(f"[DEBUG] Active rule raid_count decremented to {state['active_rule']['raid_count']}.")
        if state["active_rule"]["raid_count"] <= 0:
            try:
                user = await bot.fetch_user(state["active_rule"]["activated_by"])
            except Exception as e:
                print(f"[DEBUG] Error fetching user: {e}")
                user = None
            channel = bot.get_channel(CAMP_ANNOUNCE_ID)
            if channel and user:
                await channel.send(
                    f"{user.mention}, your special rule **{state['active_rule']['rule']}** has expired after 3 raids.")
            state["active_rule"] = {}
    db.update_game_state(state)


async def check_campaign_status(state):
    grid = state["grid"]
    friendly_count = sum(cell["state"] == "friendly_objective" for row in grid for cell in row)
    enemy_count = sum(cell["state"] == "enemy_objective" for row in grid for cell in row)
    channel = bot.get_channel(CAMP_ANNOUNCE_ID)
    if channel:
        if friendly_count == 0:
            message = (
                "Attention, troopers! All friendly HQs have been captured. "
                "The 41st Elite Corps has fallen in battle, and our beacon of hope is extinguished. "
                "We must remember this defeat as a call to rise again."
            )
            await channel.send(message)
        elif enemy_count == 0:
            message = (
                "Victory is ours, troopers! Every enemy headquarters has fallen, and the 41st Elite Corps has proven its might on the battlefield. This historic triumph reaffirms our legacy in the galaxy, and our valor will echo through the ages."
            )
            await channel.send(message)


@bot.command(name="raid_win")
@Right_role()
@commands.check(lambda ctx: ctx.channel.id == CAMP_LOGS_ID)
async def raid_win_command(ctx):
    await handle_raid_result(ctx, "win")


@bot.command(name="raid_loss")
@Right_role()
@commands.check(lambda ctx: ctx.channel.id == CAMP_LOGS_ID)
async def raid_loss_command(ctx):
    await handle_raid_result(ctx, "loss")


def invalidate_last_dir_if_out_of_bounds(fx, fy, last_dir):
    if (fx == 0 and last_dir == "north"):
        return "none"
    if (fx == 9 and last_dir == "south"):
        return "none"
    if (fy == 0 and last_dir == "west"):
        return "none"
    if (fy == 9 and last_dir == "east"):
        return "none"
    return last_dir


async def start_voting(channel):
    global voting_session_active, current_vote, vote_message_id, vote_start_time

    state = db.get_game_state()
    fx, fy = state["friendly_x"], state["friendly_y"]
    last_dir = state["last_move_direction"]

    last_dir = invalidate_last_dir_if_out_of_bounds(fx, fy, last_dir)

    opposite_dir = get_opposite_direction(last_dir)

    possible_dirs = ["north", "south", "east", "west"]

    if opposite_dir in possible_dirs:
        possible_dirs.remove(opposite_dir)

    # 2) Wände entfernen
    if fy == 0 and "north" in possible_dirs:
        possible_dirs.remove("north")
    if fy == 9 and "south" in possible_dirs:
        possible_dirs.remove("south")
    if fx == 0 and "west" in possible_dirs:
        possible_dirs.remove("west")
    if fx == 9 and "east" in possible_dirs:
        possible_dirs.remove("east")

    current_vote = {d: 0 for d in possible_dirs}
    voting_session_active = True
    vote_start_time = datetime.datetime.utcnow()

    direction_mapping = {
        "north": ("⬆️", "North"),
        "south": ("⬇️", "South"),
        "east": ("➡️", "East"),
        "west": ("⬅️", "West"),
    }
    desc_lines = []
    for d in possible_dirs:
        emoji, label = direction_mapping[d]
        desc_lines.append(f"{emoji} = {label}")

    vote_embed = discord.Embed(
        title="Voting Session",
        description=(
                "React with the direction we should move:\n\n"
                + "\n".join(desc_lines)
                + "\n\nYou have 12 hours to vote!"
        ),
        color=discord.Color.blue()
    )

    msg = await channel.send(embed=vote_embed)

    for d in possible_dirs:
        emoji, _ = direction_mapping[d]
        await msg.add_reaction(emoji)

    vote_message_id = msg.id


@bot.event
async def on_reaction_add(reaction, user):
    global voting_session_active, current_vote, vote_message_id

    if user.bot:
        return

    if voting_session_active and reaction.message.id == vote_message_id:
        emoji = reaction.emoji

        if emoji == "⬆️" and "north" in current_vote:
            current_vote["north"] += 1
        elif emoji == "⬇️" and "south" in current_vote:
            current_vote["south"] += 1
        elif emoji == "➡️" and "east" in current_vote:
            current_vote["east"] += 1
        elif emoji == "⬅️" and "west" in current_vote:
            current_vote["west"] += 1


def render_friendly_map(state):
    grid = state["grid"]
    fx, fy = state["friendly_x"], state["friendly_y"]
    ex, ey = state["enemy_x"], state["enemy_y"]

    matrix = []
    for row in range(10):
        row_symbols = []
        for col in range(10):
            cell_state = grid[col][row]["state"]
            if cell_state == "visited":
                row_symbols.append("⬛")
            elif cell_state == "friendly_objective":
                row_symbols.append("🟩")
            elif cell_state == "enemy_objective":
                row_symbols.append("🟥")
            elif cell_state == "buff_nerf":
                row_symbols.append("🟨")  # Yellow for special buff/nerf cells
            else:
                row_symbols.append("⬜")
        matrix.append(row_symbols)

    if 0 <= fx < 10 and 0 <= fy < 10:
        matrix[fy][fx] = "🟦"
    if 0 <= ex < 10 and 0 <= ey < 10:
        matrix[ey][ex] = "🟪"

    rows = ["".join(r) for r in matrix]
    return "\n".join(rows)





@bot.command()
@commands.has_permissions(administrator=True)
async def reset_campaign(ctx):
    db.reset_db()
    db.place_objectives(10, 10)
    # Get the current state and place special cells on the grid.
    state = db.get_game_state()
    state["grid"] = place_special_cells(state["grid"])
    db.update_game_state(state)
    await ctx.send("Campaign has been reset. A new map  has been created.")


@bot.command()
@commands.has_permissions(administrator=True)
async def forcemove(ctx, direction: str):
    direction = direction.lower()
    if direction not in MOVES.keys():
        await ctx.send("Invalid direction. Use north, south, east, or west.")
        return

    state = db.get_game_state()
    if can_move_back(state["last_move_direction"], direction):
        await ctx.send("Cannot immediately move back to the last square. Choose a different direction.")
        return

    old_x, old_y = state["friendly_x"], state["friendly_y"]
    new_x, new_y = single_step_move(old_x, old_y, direction)
    state["friendly_x"] = new_x
    state["friendly_y"] = new_y
    state["last_move_direction"] = direction

    if state["grid"][new_x][new_y]["state"] == "hidden":
        state["grid"][new_x][new_y]["state"] = "visited"

    # Check if the cell has a special buff/nerf
    check_special_cell(state, new_x, new_y, ctx)

    db.update_game_state(state)

    await ctx.send(f"Forced move {direction.upper()}. Friendly now at ({new_x}, {new_y}).")
    map_channel = bot.get_channel(CAMP_MAP_ID)
    updated_map = render_friendly_map(state)
    await map_channel.send("**Map updated by forcemove!**\n```\n" + updated_map + "\n```")





@bot.command()
@commands.has_permissions(administrator=True)
async def startspecialevent(ctx):
    state = db.get_game_state()
    if not state["special_event_active"]:
        state["special_event_active"] = True
        state["event_name"] = "Admin-Forced Event"
        end_time = datetime.datetime.utcnow() + datetime.timedelta(hours=5)
        state["special_event_end_time"] = end_time.isoformat()
        db.update_game_state(state)
        await ctx.send("A special event has been started forcibly!")
    else:
        await ctx.send("A special event is already active.")


@bot.command()
@commands.has_permissions(administrator=True)
async def endspecialevent(ctx):
    state = db.get_game_state()
    if state["special_event_active"]:
        state["special_event_active"] = False
        state["event_name"] = ""
        state["special_event_end_time"] = ""
        db.update_game_state(state)
        await ctx.send("The current special event has been ended.")
    else:
        await ctx.send("No active event to end.")

@bot.command()
async def status(ctx):
    state = db.get_game_state()
    msg_lines = []
    msg_lines.append(f"Wins: {state['wins']} | Losses: {state['losses']}")
    msg_lines.append(f"Friendly Position: ({state['friendly_x']}, {state['friendly_y']})")
    msg_lines.append(f"Enemy Position: ({state['enemy_x']}, {state['enemy_y']})")

    if voting_session_active:
        msg_lines.append("Voting is **active**.")
    else:
        msg_lines.append("No active voting session.")

    if state["special_event_active"]:
        msg_lines.append(f"Special Event: {state['event_name']}")
    else:
        msg_lines.append("No special event active.")

    await ctx.send("\n".join(msg_lines))


@bot.command()
async def timeleft(ctx):
    global voting_session_active, vote_start_time, vote_duration
    state = db.get_game_state()

    output_lines = []

    if voting_session_active and vote_start_time:
        now = datetime.datetime.utcnow()
        elapsed = (now - vote_start_time).total_seconds()
        remaining = vote_duration - elapsed
        if remaining > 0:
            hrs, rem = divmod(remaining, 3600)
            mins, secs = divmod(rem, 60)
            output_lines.append(f"Voting Session ends in {int(hrs)}h {int(mins)}m {int(secs)}s.")
        else:
            output_lines.append("Voting session has ended or is about to end.")

    if state["special_event_active"]:
        end_time = datetime.datetime.fromisoformat(state["special_event_end_time"])
        remaining = end_time - datetime.datetime.utcnow()
        if remaining.total_seconds() > 0:
            hrs, rem = divmod(remaining.total_seconds(), 3600)
            mins, secs = divmod(rem, 60)
            output_lines.append(f"Special Event ends in {int(hrs)}h {int(mins)}m {int(secs)}s.")
        else:
            output_lines.append("Special event is ending soon or has ended.")
    else:
        output_lines.append("No active special event.")

    await ctx.send("\n".join(output_lines))


@bot.command()
async def helpme(ctx):
    help_text = """
**Core Gameplay Commands**
1 `!stats` - Displays the current win/loss count.
2. `!raid_win` / `!raid_loss` - Logs a raid result (campain-logs only) only for CPL and above .
4. `!currentvote` - Shows current vote counts (if any).
5. `!status` - Quick summary of the current campaign state.
6. `!timeleft` - Time remaining for voting/special events.

**Buffs & Nerfs**
1. `!berfs` - lists all buffs & nerfs available
2. `!srule` - selects & activates an special rulest
3. `!aberfs` - lists active buffs & nerfs

**Special Event Commands**
1. `!currentevent` - Shows the current special event info.
2. `!events` - Lists possible events.

Use `!helpme` to see this message again.
"""
    await ctx.send(help_text)


# ---------------------------------------
# skipvote
# ---------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def skipvote(ctx):
    global voting_session_active, current_vote, vote_message_id, vote_start_time

    if not voting_session_active:
        await ctx.send("There is no active voting session to skip.")
        return

    voting_session_active = False
    sorted_votes = sorted(current_vote.items(), key=lambda x: x[1], reverse=True)
    if not sorted_votes or sorted_votes[0][1] == 0:
        await ctx.send("No votes were cast. Voting session has been ended without movement.")
        current_vote = {}
        vote_message_id = None
        vote_start_time = None
        return

    winner_direction, winner_count = sorted_votes[0]

    state = db.get_game_state()
    last_dir = state["last_move_direction"]

    old_x, old_y = state["friendly_x"], state["friendly_y"]

    if can_move_back(last_dir, winner_direction):
        if len(sorted_votes) > 1 and sorted_votes[1][1] > 0:
            winner_direction = sorted_votes[1][0]
            winner_count = sorted_votes[1][1]

    new_x, new_y = single_step_move(old_x, old_y, winner_direction)
    state["friendly_x"] = new_x
    state["friendly_y"] = new_y
    state["last_move_direction"] = winner_direction

    if state["grid"][new_x][new_y]["state"] == "hidden":
        state["grid"][new_x][new_y]["state"] = "visited"

    db.update_game_state(state)

    # >>> NEU: Check, ob Friendly auf Enemy-HQ steht <<<
    await check_if_friendly_on_enemy_hq(state)

    print(f"[DEBUG] skipvote: from ({old_x},{old_y}) -> ({new_x},{new_y}) via '{winner_direction}'")

    check_special_cell(state, new_x, new_y, None)

    await ctx.send(
        f"Voting skipped by admin. Winner was **{winner_direction.upper()}** "
        f"with {winner_count} votes. Friendly is now at ({new_x}, {new_y})."
    )

    map_channel = bot.get_channel(CAMP_MAP_ID)
    updated_map = render_friendly_map(state)
    await map_channel.send("**Map updated (vote skipped)!**\n```\n" + updated_map + "\n```")

    current_vote = {}
    vote_message_id = None
    vote_start_time = None


def render_admin_map(state):
    grid = state["grid"]
    friendly_x, friendly_y = state["friendly_x"], state["friendly_y"]
    enemy_x, enemy_y = state["enemy_x"], state["enemy_y"]

    admin_symbols = {
        "hidden": "⬜",
        "visited": "⬛",
        "friendly_objective": "🟩",
        "enemy_objective": "🟥"
    }

    matrix = []
    for y in range(10):
        row_symbols = []
        for x in range(10):
            cell_state = grid[x][y]["state"]
            symbol = admin_symbols.get(cell_state, "⬜")
            row_symbols.append(symbol)
        matrix.append(row_symbols)

    # Friendly / Enemy Marker
    if 0 <= friendly_x < 10 and 0 <= friendly_y < 10:
        matrix[friendly_y][friendly_x] = "🟦"
    if 0 <= enemy_x < 10 and 0 <= enemy_y < 10:
        matrix[enemy_y][enemy_x] = "🟪"

    rendered_rows = ["".join(r) for r in matrix]
    return "\n".join(rendered_rows)


@bot.command()
@commands.has_permissions(administrator=True)
async def mapadmin(ctx):
    state = db.get_game_state()
    admin_map_str = render_admin_map(state)

    grid = state["grid"]
    friendly_coords = []
    enemy_coords = []

    for x in range(10):
        for y in range(10):
            if grid[x][y]["state"] == "friendly_objective":
                friendly_coords.append((x, y))
            elif grid[x][y]["state"] == "enemy_objective":
                enemy_coords.append((x, y))

    friendly_list_str = ", ".join(f"({x},{y})" for (x, y) in friendly_coords) or "None"
    enemy_list_str = ", ".join(f"({x},{y})" for (x, y) in enemy_coords) or "None"

    message = (
        f"**Admin-Only Full Map**\n"
        f"```\n{admin_map_str}\n```\n"
        f"**Friendly HQ positions:** {friendly_list_str}\n"
        f"**Enemy HQ positions:** {enemy_list_str}"
    )

    await ctx.send(message)






@bot.command()
async def ping(ctx):
    await ctx.send("pong!")


def get_bot_token():
    with open('Bot-Token.txt', 'r') as file:
        return file.read().strip()


bot.run(get_bot_token())
