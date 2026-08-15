# 41st Web-Bot Repository – Antigravity IDE Instructions

## Repository

- **GitHub URL:** https://github.com/DominikLinkl/41st_web-bot-
- **Local workspace:** `c:\Users\domin\Desktop\41st_bot_rework\41st_web-bot-`
- **Main project folder:** `new_bot_structure/`

---

## Git Workflow

### 1. Pull before editing

Always pull the latest version from the remote before making any changes:

```bash
cd c:\Users\domin\Desktop\41st_bot_rework\41st_web-bot-
git pull origin main
```

### 2. Make your edits

- All bot source code lives in `new_bot_structure/`.
- Key files:
  - `main.py` — Bot entry point, role definitions, event handling
  - `database.py` — SQLite database operations (credits, purchases, etc.)
  - `utils.py` — Shared utilities, store items dict, rewards, helper functions
  - `cogs/store.py` — Store display, purchase, buy, refund commands
  - `cogs/economy.py` — Economy commands (credits, daily, gamble, etc.)
  - `cogs/utility.py` — Utility commands (profile, roster, helmet info, ranks)
  - `cogs/admin.py` — Admin-only commands
  - `cogs/moderation.py` — Moderation commands
  - `cogs/fun.py` — Fun/entertainment commands

### 3. Commit and push

```bash
git add .
git commit -m "Descriptive commit message"
git push origin main
```

---

## ⚠️ CRITICAL RULE: NEVER overwrite `credits.db`

> [!CAUTION]
> **`new_bot_structure/credits.db` must NEVER be overwritten or pushed from local.**
> This file is the live SQLite database containing all user credits, purchases, and registration data.
> It is managed exclusively by the server (the running bot instance).
> Pushing a local copy would destroy live user data.

### How to protect it:

- `credits.db` should be listed in `.gitignore` (verify this is the case).
- If git tries to stage `credits.db`, **unstage it immediately**:
  ```bash
  git reset HEAD new_bot_structure/credits.db
  ```
- If it was accidentally committed, remove it from tracking without deleting the file:
  ```bash
  git rm --cached new_bot_structure/credits.db
  git commit -m "Stop tracking credits.db"
  ```
- Never use `git add .` without checking `git status` first if you suspect `credits.db` is tracked.

---

## Project Architecture Notes

- The bot uses **discord.py** with a **Cog-based** architecture.
- `store_items` dict in `utils.py` is the single source of truth for purchasable items. If an item needs to be added/removed from the store, edit it there.
- `rewards` dict in `utils.py` (and duplicated in `main.py`) maps Discord roles to their cosmetic rewards — these are NOT store items.
- Role credit values are defined in `database.py` and duplicated in `cogs/utility.py` — keep both in sync when modifying role credits.
- The bot uses prefix commands (`!command`), not slash commands.
