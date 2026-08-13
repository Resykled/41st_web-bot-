# 41st Legion Discord Bot — Rework

A Discord bot built for the **41st Elite Corps** community (Geetsly's Gaming Network). It manages a credits economy, role-based rewards, a store system, daily streaks, moderation tools, and a collection of fun commands.

This is the **reworked version** of the bot. The original monolithic `main.py` (3,300+ lines) has been split into a clean, modular architecture using Discord.py's **Cogs** system.

**Version:** 1.8 ~ Webside  
**Bot Prefix:** `!` (case-insensitive)  
**Repository:** [github.com/DominikLinkl/41st_web-bot-](https://github.com/DominikLinkl/41st_web-bot-)

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Bot](#running-the-bot)
6. [Commands Reference](#commands-reference)
   - [Utility Commands](#-utility-cogsutilitypy)
   - [Economy Commands](#-economy-cogseconomypy)
   - [Store Commands](#-store-cogsstorepy)
   - [Moderation Commands](#-moderation-cogsmoderationpy)
   - [Admin Commands](#%EF%B8%8F-admin-cogsadminpy)
   - [Fun Commands](#-fun-cogsfunpy)
7. [Store Items & Prices](#store-items--prices)
8. [Role-Based Rank Rewards](#role-based-rank-rewards)
9. [Credit System](#credit-system)
10. [Database](#database)
11. [Allowed Channels](#allowed-channels)
12. [Deployment (Raspberry Pi)](#deployment-raspberry-pi)
13. [Contributing](#contributing)
14. [License](#license)

---

## Project Structure

```
new_bot_structure/
├── main.py                    # Entry point — bot setup, event handlers, cog loader
├── database.py                # All SQLite database operations (single source of truth)
├── utils.py                   # Shared helper functions, decorators, store items & rewards
├── bot_token.txt              # Discord bot token (not committed to git)
├── credits.db                 # SQLite database file (auto-created on first run)
├── credits.sqbpro             # DB Browser for SQLite project file
├── Regiment medals python.txt # Medal definitions with credit values
├── cogs/
│   ├── admin.py               # Bot management commands (shutdown, debug, save_db, git_push)
│   ├── economy.py             # Credits system (add, remove, daily, leader, rewards)
│   ├── fun.py                 # Fun / meme commands (rps, lean, AllStar, FunkyTown, …)
│   ├── moderation.py          # Registration & moderation (register, mute, unmute, sleep)
│   ├── store.py               # Item store & purchasing (store, buy, purchase, refund)
│   └── utility.py             # Info & helper commands (help, whoami, rules, helmets, ranks)
└── README.md                  # This file
```

---

## Prerequisites

- **Python 3.8+**
- **discord.py** v2.0+
- **pandas** (for spreadsheet operations)
- **SQLite3** (bundled with Python)

---

## Installation

1. **Clone the repository**
   ```sh
   git clone https://github.com/DominikLinkl/41st_web-bot-.git
   cd 41st_web-bot-/new_bot_structure
   ```

2. **Create a virtual environment**
   ```sh
   python3 -m venv venv
   source venv/bin/activate   # Linux / Raspberry Pi
   # or
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**
   ```sh
   pip install discord.py pandas
   ```

4. **Create the bot token file**  
   Create a file named `bot_token.txt` in the project root and paste your Discord bot token into it (one line, no quotes).

---

## Configuration

| Setting | Location | Description |
|---|---|---|
| Bot Token | `bot_token.txt` | Your Discord bot token (one line, no quotes) |
| Command Prefix | `main.py` | Default `!` — configurable in the `commands.Bot()` call |
| Case Sensitivity | `main.py` | Set to `case_insensitive=True` — `!Hello` and `!hello` both work |
| Allowed Channels | `utils.py` | Bot commands restricted to `bot-commands`, `bot-test`, and `econ-chat` |
| Bug Report Channel | `utils.py` | Reports go to the `bug-reports` channel |
| Database | `credits.db` | Auto-created by `database.py` on first import |

---

## Running the Bot

```sh
source venv/bin/activate     # Activate the virtual environment first!
python main.py
```

On startup, the bot will:
1. Initialize the SQLite database (create tables if they don't exist).
2. Dynamically load all Cogs from the `cogs/` directory.
3. Sync credits for all members across connected servers.
4. Send a startup embed to the `bot-commands` channel showing the version and startup time.

---

## Commands Reference

All commands use the `!` prefix and are **case-insensitive**.

Legend:
- 🟢 = Available to all registered users
- 🟡 = Requires specific roles (see "Required Roles" column)
- 🔴 = Technical Commander only

---

### 🔧 Utility (`cogs/utility.py`)

| Command | Access | Required Roles | Description |
|---|---|---|---|
| `!hello` | 🟢 | — | Bot sends a greeting embed |
| `!report <problem>` | 🟢 | — | Report a bug or issue to the `bug-reports` channel |
| `!version` | 🟢 | — | Show the current bot version and update date |
| `!help` | 🟢 | — | List all available commands (admin commands shown only to admins) |
| `!website` | 🟢 | — | Link to the 41st website (geetslys41st.com) |
| `!oldest` | 🟢 | — | Easter egg for the first server member |
| `!whoami` | 🟢 | — | Shows subcommand menu |
| `!whoami medals` | 🟢 | — | Lists all your medals from Army, SOF, and Regiment servers |
| `!whoami purchases` | 🟢 | — | Lists all your store purchases |
| `!whoami stats` | 🟢 | — | Shows username, join date, rank, and credit breakdown |
| `!whoami credits` | 🟢 | — | Full credit breakdown: medals, qualifications, purchases, rewards |
| `!uptime` | 🟢 | — | Shows how long the bot has been running |
| `!show_quals` | 🟡 | SOF Staff | Shows all qualifications sorted by platform (PC/Xbox/PS) |
| `!ct_number` | 🟡 | Staff Sergeant+ | Generates a unique random CT number (1000–9999) |
| `!rules [1-11]` | 🟢 | — | Display server rules by category |
| `!helmets [@user]` | 🟢 | — | Show eligible helmets and attachments based on roles & purchases |
| `!ranks [1-14]` | 🟢 | — | Show rank hierarchy and descriptions |
| `!id @user` | 🟡 | Economy Admin / Economy Lead / Commander / Technical Commander | Show detailed user info (ID, credits, join date) |

#### Rules Categories

| # | Topic |
|---|---|
| 1 | Army Raid Rules |
| 2 | Skin Rules |
| 3 | Server Guidelines |
| 4 | Community Rules |
| 5 | Unruly Behavior Guidelines |
| 6 | Staff Expectations |
| 7 | Hosting a Raid |
| 8 | Running a Raid |
| 9 | Emergency Situations |
| 10 | Rank Hierarchy |
| 11 | Strike System + Discipline |

---

### 💰 Economy (`cogs/economy.py`)

| Command | Access | Required Roles | Description |
|---|---|---|---|
| `!credits` | 🟢 | — | Shows your current credit balance |
| `!daily` | 🟢 | — | Claim daily credits (base 50, max 80 with streak). Resets if you miss 48h |
| `!leader` | 🟢 | — | Show the top 5 daily streak leaderboard + your position |
| `!rewards` | 🟢 | — | Show your unlocked rank-based rewards |
| `!check_credits @user` | 🟡 | Economy Admin / Economy Lead / Commander / Technical Commander | View another user's credit details (current, max, removed) |
| `!add @user <amount> [comment]` | 🟡 | Economy Admin / Economy Lead / Commander / Technical Commander | Add credits to a user. Logged in `database-activity` channel |
| `!remove @user <amount> [comment]` | 🟡 | Economy Admin / Economy Lead / Commander / Technical Commander | Remove credits from a user. Logged in `database-activity` channel |
| `!setUserCredits @user <amount> [comment]` | 🟡 | Economy Lead / Commander / Technical Commander | Set a user's credits to an exact value |

---

### 🛒 Store (`cogs/store.py`)

| Command | Access | Required Roles | Description |
|---|---|---|---|
| `!store` | 🟢 | — | Show store category overview |
| `!store <1-5>` | 🟢 | — | Browse items in a specific price category |
| `!store 0` | 🟢 | — | View all store items (sent via DM) |
| `!ggn_store` | 🟢 | — | Show GGN store credit-to-USD conversion rates |
| `!purchase <item>` | 🟢 | — | Purchase an item for yourself (deducts credits) |
| `!buy @user <item>` | 🟡 | Economy Lead / Commander / Technical Commander | Purchase an item for another user |
| `!useritems @user` | 🟡 | Technical Commander / Republic Droids / Commander / Economy Lead / Economy Admin / Art Team | View all items a user has purchased |
| `!refund @user <item>` | 🟡 | Technical Commander / Republic Droids / Economy Lead / Commander | Refund an item and return credits to the user |

#### Store Categories

| Category | Price Range | Command |
|---|---|---|
| 1 | 7,500 credits | `!store 1` |
| 2 | 10,000 credits | `!store 2` |
| 3 | 15,000–20,000 credits | `!store 3` |
| 4 | 30,000–35,000 credits | `!store 4` |
| 5 | 40,000–50,000 credits | `!store 5` |

---

### 🔨 Moderation (`cogs/moderation.py`)

| Command | Access | Required Roles | Description |
|---|---|---|---|
| `!register` | 🟢 | — | Register yourself in the bot system (one-time, calculates initial credits from roles) |
| `!registerRemove @user` | 🔴 | Technical Commander | Reset a user's registration so they can re-register |
| `!registerEveryone` | 🔴 | Technical Commander | Bulk-register all members with the Clone Trooper role |
| `!removeNonCTs` | 🔴 | Technical Commander | Remove all users without the Clone Trooper role from the database |
| `!removeARCTroopers` | 🔴 | Technical Commander | Remove all users with the ARC Trooper role from the database |
| `!resetStats @user` | 🔴 | Technical Commander | Reset all stats for a specific user |
| `!sleep <duration>` | 🟢 | — | Timeout yourself for a set duration (e.g. `!sleep 7h`, `!sleep 1h 30min`). Max 24h |
| `!mute @user <duration>` | 🟡 | Economy Admin / Economy Lead / Commander / Technical Commander / SGM / 2LT / LT / CPT / MAJ / High Command | Mute a member (e.g. `!mute @user 5d 10h`) |
| `!unmute @user` | 🟡 | Economy Admin / Economy Lead / Commander / Technical Commander / SGM / 2LT / LT / CPT / MAJ / High Command | Remove timeout from a member |

---

### ⚙️ Admin (`cogs/admin.py`)

| Command | Access | Required Roles | Description |
|---|---|---|---|
| `!save_db` | 🔴 | Technical Commander | Save a backup of the database |
| `!shutdown` | 🔴 | Technical Commander | Save the database and gracefully shut down the bot |
| `!kill` | 🔴 | Technical Commander | Save the database and restart the bot via shell script |
| `!cleardb` | 🔴 | Technical Commander | **⚠️ DANGER** — Wipes all data from the database |
| `!debug` | 🔴 | Technical Commander | Run automated tests on all major commands |
| `!git_push [branch]` | 🔴 | Technical Commander | Push current changes to GitHub (default branch: `main-information`) |
| `!Test` | 🟢 | — | Simple test command (sends a greeting embed) |
| `!test_chat` | 🟢 | — | Debug channel permissions (output in console) |

---

### 🎮 Fun (`cogs/fun.py`)

| Command | Access | Description |
|---|---|---|
| `!rps <rock/paper/scissors>` | 🟢 | Play rock-paper-scissors with the bot |
| `!please <request>` | 🟢 | Ask the bot nicely — it responds politely |
| `!lean` | 🟢 | Random lean meme GIF (only in specific server/channels) |
| `!FunkyTown` | 🟢 | Sends the "Funkytown" lyrics line by line with a GIF |
| `!AllStar` | 🟢 | Sends "All Star" (Smash Mouth) lyrics line by line with Shrek GIF |
| `!techno` | 🟢 | Techno YouTube link |
| `!drugs` | 🟢 | "Deathsticks?" response |
| `!ra` | 🟢 | Sends a GIF |
| `!kyoda` | 🟢 | Fake timeout error message |
| `!Sykles` | 🟢 | Easter egg message |
| `!froger` | 🟢 | Frog jumpscare GIF |
| `!bitches` | 🟢 | "you have no bitches" |
| `!water` | 🟢 | "Water IS wet" + YouTube link |
| `!no_you` | 🟢 | Sends the Navy Seal copypasta |
| `!monte` | 🟢 | Pings a specific user telling them to touch grass |
| `!gravestone` | 🟢 | Pings a specific user |
| `!nuke` | 🟢 | Pings a specific user |

---

## Store Items & Prices

| Item | Price (Credits) |
|---|---|
| Flashlight | 7,500 |
| Antenna | 7,500 |
| Communicator | 7,500 |
| Heavy Attachments | 7,500 |
| Rangefinder Down | 7,500 |
| Helmet Tubes | 7,500 |
| Binoculars | 10,000 |
| Binoculars Up | 10,000 |
| Flight Computer | 15,000 |
| Clone Gunner | 20,000 |
| Hood | 20,000 |
| ARF | 30,000 |
| Snowtrooper/Flametrooper | 30,000 |
| Custom Visor | 30,000 |
| Render | 30,000 |
| BARC | 35,000 |
| Phase 1 | 35,000 |
| 2003 Helmets | 40,000 |
| Desert | 45,000 |
| Halfbody | 50,000 |
| Airborne | 50,000 |
| Republic Commando | 60,000 |
| Full Body | 85,000 |

### GGN Store Credit-to-USD Conversions

| Credits | USD |
|---|---|
| 7,500 | $5.00 |
| 10,000 | $7.50 |
| 12,500 | $10.00 |
| 15,000 | $12.50 |
| 20,000 | $15.00 |
| 25,000 | $20.00 |
| 30,000 | $25.00 |
| 40,000 | $30.00 |
| 45,000 | $30.00 |

---

## Role-Based Rank Rewards

| Role | Rewards |
|---|---|
| Art Team | Bad Batch Echo helmet |
| Art Team Veteran | Store items for 10k and under are free |
| Clone Trooper | White and green colour on the helmet |
| Veteran Trooper | Camouflage and grey on the helmet |
| Sergeant | Rangefinder, tiny amount of extra colour (no pink and gold) |
| 2nd Lieutenant | Custom Visor (no gold, white and pink), small amount of extra colour (no gold) |
| Lieutenant | Custom Visor (no gold, white and pink), small amount of extra colour (no gold) |
| Captain | Halfbody, Custom Visor can be gold/pink, gold on the armour |
| Major | Halfbody, Custom Visor can be gold/pink, gold on the armour |
| Technical Commander | Halfbody, Custom Visor can be gold/pink, gold on the armour |
| High Command | Visor Glow, white visor |
| ARC Trooper | Decent amount of extra colour, green still has to be the main colour |
| Republic Commando | Decent amount of extra colour, green still has to be the main colour |

---

## Credit System

Credits are the bot's economy currency. They are earned through:

1. **Roles** — Each qualifying role grants a set amount of credits:
   - **Stacking roles**: Credits from multiple roles are added together (medals, qualifications)
   - **Non-stacking roles**: Only the highest-value role counts (rank roles like Clone Trooper → Commander)

2. **Daily Claims** (`!daily`) — Base reward of 50 credits, increases with streak up to 80 credits. Streak resets after 48 hours of inactivity.

3. **Admin Grants** — Admins can add/remove/set credits manually with `!add`, `!remove`, and `!setUserCredits`.

Credits are spent in the **store** on helmet attachments, skins, and cosmetic upgrades.

### Multi-Server Sync

The bot tracks roles across **three servers**:
- Army Server (`850840453800919100`)
- SOF Server (`911409562970628167`)
- Regiment Server (`1138926753931346090`)

When roles change on any server, the bot automatically recalculates and updates credits.

---

## Database

The bot uses an **SQLite** database (`credits.db`) managed entirely through `database.py`. All database functions are centralized there — no other file directly executes SQL.

### Tables

| Table | Purpose |
|---|---|
| `user_credits` | Current, max, and removed credits per user |
| `role_credits` | Credit value assigned to each stacking role |
| `non_stacking_role_credits` | Credit value for non-stacking roles (highest wins) |
| `role_status` | Tracks which roles have been credited to a user |
| `register_status` | Tracks user registration state |
| `user_roles` | Caches roles per user per server |
| `user_daily` | Daily claim timestamp and streak counter |
| `user_medals` | Medals awarded to users |
| `user_purchases` | Store purchase history |
| `update_status` | Tracks one-time migration updates |
| `reminders` | User reminder preferences |

### Key Functions

- **Credits**: `get_user_credits()`, `update_user_credits()`, `reset_user_stats()`
- **Roles**: `add_role_credits()`, `remove_role_credits()`, `mark_role_credited()`, `check_role_credited()`
- **Daily**: `get_user_daily_info()`, `update_user_daily_info()`, `get_top_streaks()`
- **Store**: `get_user_purchases()`, `add_user_purchase()`, `remove_user_purchase()`
- **Registration**: `has_registered()`, `mark_as_registered()`, `remove_registered_status()`
- **Backup**: `save_database()`

---

## Allowed Channels

Commands can only be used in these channels (configured in `utils.py`):

| Channel | Purpose |
|---|---|
| `bot-commands` | Primary command channel |
| `bot-test` | Testing channel |
| `econ-chat` | Economy discussion channel |
| `bug-reports` | Destination for `!report` messages |
| `database-activity` | Automated log for credit add/remove operations |
| `lean-zone` | Additional channel for the `!lean` command |

---

## Deployment (Raspberry Pi)

The bot is designed to run on a Raspberry Pi. To start it:

```sh
cd /home/dominik/DiscordBot/new_bot_structure
source venv/bin/activate
python main.py
```

> **Important:** Always activate the virtual environment (`source venv/bin/activate`) before running the bot, otherwise Python won't find the installed packages like `discord.py`.

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Commit your changes (`git commit -am 'Add my feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Open a Pull Request.

---

## License

This project is licensed under the **MIT License**.
