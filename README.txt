
# Discord Bot for 41st Legion

This Discord bot is designed for managing and interacting with members of the 41st Legion. It provides various commands and functionalities to manage roles, credits, medals, and more.

## Table of Contents
1. [Installation](#installation)
2. [Setup](#setup)
3. [Commands](#commands)
4. [Database](#database)
5. [Contributing](#contributing)
6. [License](#license)

## Installation

### Prerequisites
- Python 3.8 or higher
- Discord.py library
- SQLite

### Steps

1. **Clone the Repository**
    ```sh
    git clone https://github.com/Resykled/Discord.Bot.41st.git
    cd Discord.Bot.41st
    ```

2. **Install Dependencies**
    ```sh
    pip install -r requirements.txt
    ```

3. **Set Up Environment Variables**
    - Create a `bot-token.txt` file in the root directory and paste your Discord bot token in it.

4. **Initialize the Database**
    - Ensure the `database.py` script is executed to set up the necessary database tables.

## Setup

### Configuration

1. **Bot Token**
    - Ensure your bot token is correctly placed in the `bot-token.txt` file.

2. **Database**
    - The bot uses an SQLite database (`credits.db`). Make sure this file is accessible and properly set up by running the `database.py` script.

### Running the Bot

```sh
python main.py
```

## Commands

### General Commands
- `!hello` - Greets the user.
- `!report <problem>` - Reports an issue to the designated channel.
- `!report_bug <problem>` - Specifically report a bug.

### Credit Management
- `!daily` - Claims daily credits. The bot also shows the remaining time until the user can claim again.
- `!leader` - Shows the top 5 users with the highest daily streaks and the user's position if they are not in the top 5.
- `!git_push` - Force pushes all changes to the GitHub repository.

## Database

The database (`credits.db`) is managed using SQLite and is accessed through the `database.py` script. It includes tables for user credits, role credits, daily claims, and more.

### Tables

- `user_credits` - Stores the credits for each user.
- `role_credits` - Stores the credits associated with each role.
- `user_daily` - Stores the daily claim information for users.
- `role_status` - Tracks roles credited to users.
- `register_status` - Tracks registration status of users.
- `user_medals` - Stores medals awarded to users.
- `user_purchases` - Tracks purchases made by users.

### Important Functions

- **Credits Management**
  - `get_user_credits(user_id)`
  - `update_user_credits(user_id, current_credits)`
  - `reset_user_stats(user_id)`

- **Role Management**
  - `add_role_credits(role_name, credit_amount)`
  - `remove_role_credits(role_name)`

- **Daily Claims**
  - `get_user_daily_info(user_id)`
  - `update_user_daily_info(user_id, last_claim, streak)`

- **Leaderboard**
  - `get_top_streaks(limit=5)`
  - `get_user_position(user_id)`

## Contributing

Contributions are welcome! Please follow the standard GitHub flow for contributing:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License.
