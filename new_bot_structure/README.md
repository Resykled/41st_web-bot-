# 41st Legion Discord Bot — Rework

A Discord bot built for the **41st Elite Corps** community. It manages a credits economy, role-based rewards, a store, daily streaks, moderation tools, and a collection of fun commands.

This is the **reworked version** of the bot. The original monolithic `main.py` (3 300+ lines) has been split into a clean, modular architecture using Discord.py's **Cogs** system.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Bot](#running-the-bot)
6. [Commands Overview](#commands-overview)
7. [Database](#database)
8. [Contributing](#contributing)
9. [License](#license)

---

## Project Structure

```
new_bot_structure/
├── main.py            # Entry point — bot setup, event handlers, cog loader
├── database.py        # All SQLite database operations (single source of truth)
├── utils.py           # Shared helper functions & decorators
├── credits.db         # SQLite database file (auto-created on first run)
├── cogs/
│   ├── admin.py       # Bot management commands (shutdown, debug, save_db, …)
│   ├── economy.py     # Credits system (add, remove, daily, leader, rewards, …)
│   ├── fun.py         # Fun / meme commands (rps, lean, AllStar, FunkyTown, …)
│   ├── moderation.py  # Moderation & registration (mute, unmute, register, …)
│   ├── store.py       # Item store & purchasing (store, buy, purchase, refund, …)
│   └── utility.py     # Info & helper commands (help, whoami, rules, helmets, ranks, …)
└── README.md          # This file
```

---

## Prerequisites

- **Python 3.8+**
- **discord.py** (v2.0+)
- **pandas** (for spreadsheet operations)
- **SQLite3** (bundled with Python)

---

## Installation

1. **Clone the repository**
   ```sh
   git clone https://github.com/Resykled/Discord.Bot.41st.git
   cd Discord.Bot.41st
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
   > If no `requirements.txt` exists yet, install manually:
   > ```sh
   > pip install discord.py pandas
   > ```

3. **Create the bot token file**
   Create a file named `bot_token.txt` in the project root and paste your Discord bot token into it (nothing else).

---

## Configuration

| Setting | Location | Description |
|---|---|---|
| Bot Token | `bot_token.txt` | Your Discord bot token (one line, no quotes) |
| Command Prefix | `main.py` | Default `!` — configurable in the `commands.Bot()` call |
| Case Sensitivity | `main.py` | Set to `case_insensitive=True` — `!Hello` and `!hello` both work |
| Allowed Channels | `main.py` | Bot commands restricted to `bot-test` and `bot-commands` channels |
| Database | `credits.db` | Auto-created by `database.py` on first import |

---

## Running the Bot

```sh
python main.py
```

On startup, the bot will:
1. Initialize the SQLite database (create tables if they don't exist).
2. Dynamically load all Cogs from the `cogs/` directory.
3. Sync credits for all members across connected servers.
4. Send a startup embed to the `bot-commands` channel.

---

## Commands Overview

All commands use the `!` prefix and are **case-insensitive**.

### 🛡️ Admin (`cogs/admin.py`)

| Command | Description |
|---|---|
| `!shutdown` | Gracefully shuts down the bot |
| `!kill` | Force-kills the bot process |
| `!cleardb` | Resets the entire database (**use with caution**) |
| `!save_db` | Saves a backup of the database |
| `!git_push [branch]` | Pushes changes to GitHub |
| `!debug` | Toggles debug mode |
| `!test_chat` | Debug channel output |
| `!Test` | Test command |

### 💰 Economy (`cogs/economy.py`)

| Command | Description |
|---|---|
| `!credits` | Shows your current credits |
| `!check_credits @user` | Check another user's credits |
| `!add @user <amount> [comment]` | Add credits to a user |
| `!remove @user <amount> [comment]` | Remove credits from a user |
| `!setUserCredits @user <amount>` | Set a user's credits to an exact value |
| `!daily` | Claim daily credits (streak system) |
| `!leader` | Show the top 5 daily streak leaderboard |
| `!rewards` | Show role-based rewards |

### 🛒 Store (`cogs/store.py`)

| Command | Description |
|---|---|
| `!ggn_store` | Shows the GGN store |
| `!store [category]` | Browse the item store by category |
| `!purchase <item>` | Purchase an item for yourself |
| `!buy @user <item>` | Purchase an item for another user |
| `!useritems @user` | View a user's purchased items |
| `!refund @user <item>` | Refund an item purchase |

### 🎮 Fun (`cogs/fun.py`)

| Command | Description |
|---|---|
| `!rps <rock/paper/scissors>` | Play rock-paper-scissors with the bot |
| `!lean` | Lean meme |
| `!FunkyTown` | Funky Town lyrics |
| `!AllStar` | All Star lyrics |
| `!please <request>` | Ask the bot nicely |
| `!gravestone` | Gravestone meme |
| `!nuke` | Nuke meme |
| `!techno`, `!drugs`, `!ra`, `!kyoda`, `!Sykles`, `!froger`, `!bitches`, `!water`, `!no_you`, `!monte` | Various fun/meme commands |

### 🔧 Utility (`cogs/utility.py`)

| Command | Description |
|---|---|
| `!hello` | Bot greets the user |
| `!report <problem>` | Report a bug or issue |
| `!version` | Show the bot version |
| `!help` | Custom help command |
| `!id @user` | Show a user's Discord ID and info |
| `!website` | Link to the 41st website |
| `!oldest` | Show the oldest member |
| `!whoami [subcommand]` | Detailed user profile |
| `!uptime` | Show bot uptime |
| `!show_quals` | Show available qualifications and costs |
| `!ct_number` | Show clone trooper numbering |
| `!rules [category]` | Display server rules |
| `!helmets [@user]` | Show helmet customization options |
| `!ranks [number]` | Show rank information |

### 🔨 Moderation (`cogs/moderation.py`)

| Command | Description |
|---|---|
| `!register` | Register yourself in the bot system |
| `!registerRemove @user` | Remove a user's registration |
| `!registerEveryone` | Bulk-register all server members |
| `!removeNonCTs` | Remove non-Clone Trooper registrations |
| `!removeARCTroopers` | Remove ARC Trooper registrations |
| `!resetStats @user` | Reset a user's stats |
| `!sleep <duration>` | Self-mute for a set duration |
| `!mute @user <duration>` | Mute a member |
| `!unmute @user` | Unmute a member |

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
- **Store**: `get_user_purchases()`, `get_user_medals()`
- **Registration**: `has_registered()`, `mark_as_registered()`, `remove_registered_status()`

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
