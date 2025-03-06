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
CAMP_MAP_ID = 1338952160657932339
CAMP_ANNOUNCE_ID = 1338952435921584138
CAMP_LOGS_ID = 1338951678468296835
CAMP_COMMANDS_ID = 1338952906052997204
# ------------------------------------------

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
    "Good work troopers! With that objective achieved we've made a significant breakthrough on liberating this planet...",
    "Excellent shooting men! With the enemy defeated for now, we can continue our advance...",
    "Fleet reports enemy signatures dropping, whoever's left is on the run...",
    "Excellent work men! We're one step closer to taking this planet for the Republic...",
    "Look at those seppies run! Troopers, rally together and lets demolish the rest of them...",
    "Air support is on the way to help with clean-up, late as usual to the party!...",
    "That did it troopers! The clankers are in a full-scale retreat...",
    "Word has it that Republic Commandos were able to break through...",
    "Get heavy weapons set up troopers! We've won the day, but those droids are absolutely going to be working their way back...",
    "Heavy armor is obliterating the last of the enemy forces as they attempt to make their escape..."
]

LOSS_ANNOUNCEMENTS = [
    "Pack it up men, we've lost too many brothers to continue the offensive...",
    "We did what we could troopers, but the Seppies have us beat this time...",
    "Heads down! Our vanguard just got blasted and now they're coming for us...",
    "Mission failed men, we couldn't crack the droids. They're using this as an opportunity to push us hard...",
    "Buckle up troopers, we're in for the fight of our lives now...",
    "Take cover men! Venators in orbit are providing an orbital bombardment for us to make our retreat...",
    "Commando droids just took out our left flank and are about to make contact!",
    "Those droidekas have tough shields! They're counterpushing with those rollers...",
    "Those supers have tough armor! They're breaking through our forward positions...",
    "That's it men, we've lost too many troopers to continue the push..."
]


def is_Technical_Commander():
    async def predicate(ctx):
        bot_dev_role = discord.utils.get(ctx.guild.roles, name="Technical Commander")
        if bot_dev_role in ctx.author.roles:
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

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    # Optionally, start background tasks
    daily_event_check.start()
    vote_check_loop.start()
    hq_event_check_loop.start()


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
    # Altes Feld auf "visited" setzen
    grid[old_x][old_y]["state"] = "visited"

    # Alle möglichen Zellen sammeln, die kein HQ sind
    possible_cells = []
    for x in range(10):
        for y in range(10):
            if grid[x][y]["state"] not in ["friendly_objective", "enemy_objective"]:
                possible_cells.append((x, y))

    # Falls es gar keinen freien Platz gibt, brechen wir ab
    if not possible_cells:
        return (old_x, old_y)

    # Zufällige neue Position wählen
    new_x, new_y = random.choice(possible_cells)
    grid[new_x][new_y]["state"] = "enemy_objective"
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


async def finish_hq_event(state, success):
    hq_event = state["hq_event"]
    grid = state["grid"]

    print(f"[DEBUG] finish_hq_event: Ending HQ event of type {hq_event['type']} with success = {success}.")

    if success:
        if hq_event["type"] == "attack":
            grid[hq_event["target_x"]][hq_event["target_y"]]["state"] = "friendly_objective"
            print(f"[DEBUG] finish_hq_event: Enemy HQ captured at ({hq_event['target_x']}, {hq_event['target_y']}).")
        text_snippet = random.choice(WIN_ANNOUNCEMENTS)
    else:
        text_snippet = random.choice(LOSS_ANNOUNCEMENTS)

    if hq_event["type"] == "defense":
        if success:
            announcement = (
                "Defense SUCCESS! The friendly HQ has been saved! "
                "However, it will no longer trigger another event."
            )
        else:
            announcement = (
                "Defense FAILED! The friendly HQ was overrun and removed from the map!"
            )
        grid[hq_event["target_x"]][hq_event["target_y"]]["state"] = "visited"
        print(
            f"[DEBUG] finish_hq_event: Defense ended at ({hq_event['target_x']}, {hq_event['target_y']}). Marker removed.")
    else:
        if not success:
            old_x = hq_event["target_x"]
            old_y = hq_event["target_y"]
            reposition_enemy_hq(grid, old_x, old_y)
            announcement = (
                "We were not able to capture the enemy HQ in time. "
                "The enemy got reinforcements and repositioned!"
            )
            print(f"[DEBUG] finish_hq_event: Attack failed; enemy HQ repositioned from ({old_x},{old_y}).")
        else:
            announcement = "Attack SUCCESS! The enemy HQ has been captured!"

    channel = bot.get_channel(CAMP_ANNOUNCE_ID)
    if channel:
        await channel.send(f"{announcement}\n{text_snippet}")
    else:
        print("[DEBUG] finish_hq_event: CAMP_ANNOUNCE_ID channel not found.")

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

    # Check campaign status after finishing HQ event
    await check_campaign_status(state)


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
        if state["losses"] >= 10:
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
@commands.check(lambda ctx: ctx.channel.id == CAMP_LOGS_ID)
async def raid_win_command(ctx):
    await handle_raid_result(ctx, "win")


@bot.command(name="raid_loss")
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
    if fx == 0 and "north" in possible_dirs:
        possible_dirs.remove("north")
    if fx == 9 and "south" in possible_dirs:
        possible_dirs.remove("south")
    if fy == 0 and "west" in possible_dirs:
        possible_dirs.remove("west")
    if fy == 9 and "east" in possible_dirs:
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

    # matrix[row][col]
    matrix = []
    for row in range(10):
        row_symbols = []
        for col in range(10):
            cell_state = grid[col][row]["state"]  # col=x, row=y
            if cell_state == "visited":
                row_symbols.append("⬛")
            elif cell_state == "friendly_objective":
                row_symbols.append("🟩")
            elif cell_state == "enemy_objective":
                row_symbols.append("🟥")
            else:
                row_symbols.append("⬜")
        matrix.append(row_symbols)

    # Friendly Marker
    if 0 <= fx < 10 and 0 <= fy < 10:
        matrix[fy][fx] = "🟦"

    # Enemy Marker
    if 0 <= ex < 10 and 0 <= ey < 10:
        matrix[ey][ex] = "🟪"

    rows = ["".join(r) for r in matrix]
    return "\n".join(rows)


@bot.command()
async def map(ctx):
    """
    Displays the discovered map with a legend.
    """
    state = db.get_game_state()
    friendly_map_str = render_friendly_map(state)

    legend = """
Legend:
⬜ - Hidden
⬛ - Visited
🟩 - Friendly Objective
🟥 - Enemy Objective
🟦 - Friendly Marker
🟪 - Enemy Marker (only if adjacent)
"""

    await ctx.send(f"```\n{friendly_map_str}\n```{legend}")


@bot.command()
async def stats(ctx):
    state = db.get_game_state()
    await ctx.send(f"Wins: {state['wins']} | Losses: {state['losses']}")


@bot.command()
async def currentvote(ctx):
    if voting_session_active:
        standings = "\n".join([f"{dir.title()}: {count}" for dir, count in current_vote.items()])
        await ctx.send(f"**Current Vote Standings**:\n{standings}")
    else:
        await ctx.send("No active voting session.")


@bot.command()
async def objectives(ctx):
    state = db.get_game_state()
    grid = state["grid"]
    friendly_count = sum(cell["state"] == "friendly_objective" for row in grid for cell in row)
    enemy_count = sum(cell["state"] == "enemy_objective" for row in grid for cell in row)

    await ctx.send(
        f"Friendly Objectives Remaining: {friendly_count}\n"
        f"Enemy Objectives Remaining: {enemy_count}"
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    db.reset_db()
    db.place_objectives(10, 10)
    await ctx.send("Campaign has been reset. A new map has been created.")


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

    db.update_game_state(state)

    # >>> NEU: Check, ob Friendly auf Enemy-HQ steht <<<
    await check_if_friendly_on_enemy_hq(state)

    await ctx.send(f"Forced move {direction.upper()}. Friendly now at ({new_x}, {new_y}).")

    map_channel = bot.get_channel(CAMP_MAP_ID)
    updated_map = render_friendly_map(state)
    await map_channel.send("**Map updated by forcemove!**\n```\n" + updated_map + "\n```")


@bot.command()
@commands.has_permissions(administrator=True)
async def position(ctx):
    state = db.get_game_state()
    await ctx.send(
        f"Friendly Position: ({state['friendly_x']}, {state['friendly_y']})\n"
        f"Enemy Position: ({state['enemy_x']}, {state['enemy_y']})"
    )


@bot.command()
async def currentevent(ctx):
    state = db.get_game_state()
    if state["special_event_active"]:
        end_time = datetime.datetime.fromisoformat(state["special_event_end_time"])
        remaining = end_time - datetime.datetime.utcnow()
        hours, remainder = divmod(remaining.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)

        await ctx.send(
            f"**Current Event**: {state['event_name']}\n"
            f"**Time Remaining**: {int(hours)}h {int(minutes)}m"
        )
    else:
        await ctx.send("No special event is active right now.")


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
async def events(ctx):
    await ctx.send("**Possible Events**:\n1) Double Progress\n2) Enemy Reinforcements\n3) Friendly Backup")


@bot.command()
async def viewgrid(ctx):
    state = db.get_game_state()
    grid_str = str(state["grid"])

    chunk_size = 1900
    for i in range(0, len(grid_str), chunk_size):
        chunk = grid_str[i: i + chunk_size]
        await ctx.send(f"```{chunk}```")


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
@is_Technical_Commander()
async def helpme(ctx):
    help_text = """
**Core Gameplay Commands**
1. `!map` - Shows discovered (visited) parts of the map.
2. `!stats` - Displays the current win/loss count.
3. `!raid_win` / `!raid_loss` - Logs a raid result (campain-logs only).
4. `!objectives` - Shows how many friendly/enemy objectives remain.
5. `!currentvote` - Shows current vote counts (if any).
6. `!status` - Quick summary of the current campaign state.
7. `!timeleft` - Time remaining for voting/special events.

**Special Event Commands**
1. `!currentevent` - Shows the current special event info.
2. `!events` - Lists possible events (placeholder).
3. `!startspecialevent` / `!endspecialevent` (Admin) - Manage events.

**Administrative Commands**
1. `!reset` - Resets the entire campaign (map, stats, etc.).
2. `!forcemove <direction>` - Forces a friendly marker move for testing.
3. `!viewgrid` - Shows the raw grid JSON data.
4. `!position` - Shows the friendly/enemy positions.
5. `!mapadmin` - Shows the full admin map (HQ, enemy, etc.).
6. `!skipvote` - Ends voting session early, admin only.

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
