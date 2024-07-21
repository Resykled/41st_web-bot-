import sqlite3
import time
import threading
import logging

# Einrichtung des Loggings
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Globale Lock-Variable
db_lock = threading.Lock()

def create_connection():
    connection = sqlite3.connect('credits.db')
    connection.execute("PRAGMA busy_timeout = 10000")  # Warte bis zu 10000ms (10 Sekunden), wenn die DB gesperrt ist
    return connection

def create_update_status_table():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS update_status (
            user_id INTEGER PRIMARY KEY
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

create_update_status_table()

def has_been_updated(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT user_id FROM update_status WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result is not None

def mark_as_updated(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO update_status (user_id) VALUES (?)', (user_id,))
        connection.commit()
        cursor.close()
        connection.close()

def create_tables():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_credits (
        user_id INTEGER PRIMARY KEY,
        current_credits INTEGER NOT NULL,
        max_credits INTEGER NOT NULL,
        removed_credits INTEGER NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_credits (
            role_name TEXT PRIMARY KEY,
            credit_amount INTEGER NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS non_stacking_role_credits (
            role_name TEXT PRIMARY KEY,
            credit_amount INTEGER NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER,
            server_id INTEGER,
            role_name TEXT,
            PRIMARY KEY (user_id, server_id, role_name)
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

# Call these functions to ensure the table and columns exist
create_tables()

def add_column_if_not_exists():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(user_credits)")
        columns = [info[1] for info in cursor.fetchall()]
        if "removed_credits" not in columns:
            cursor.execute("ALTER TABLE user_credits ADD COLUMN removed_credits INTEGER NOT NULL DEFAULT 0")
        connection.commit()
        cursor.close()
        connection.close()

# Call these functions to ensure the table and columns exist
create_tables()
add_column_if_not_exists()

def create_role_status_table():
    with db_lock:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_status (
            user_id INTEGER,
            role_name TEXT,
            credited INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, role_name)
        )
        ''')
        conn.commit()
        cursor.close()
        conn.close()

create_role_status_table()  # Rufen Sie diese Funktion auf, um die Tabelle zu erstellen

def mark_role_credited(user_id, role_name):
    with db_lock:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO role_status (user_id, role_name, credited) VALUES (?, ?, 1) ON CONFLICT(user_id, role_name) DO UPDATE SET credited=1', (user_id, role_name))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Marked role {role_name} as credited for user {user_id}")

def unmark_role_credited(user_id, role_name):
    with db_lock:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE role_status SET credited = 0 WHERE user_id = ? AND role_name = ?', (user_id, role_name))
        conn.commit()
        cursor.close()
        conn.close()


def check_role_credited(user_id, role_name):
    with db_lock:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT credited FROM role_status WHERE user_id = ? AND role_name = ?', (user_id, role_name))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result and result[0] == 1

def get_user_credits(user_id, roles, role_credits, non_stacking_roles):
    unique_roles = set(role.name for role in roles)

    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT current_credits, max_credits, removed_credits FROM user_credits WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

    if result:
        current_credits, max_credits, removed_credits = result
        role_credits_sum = sum(role_credits.get(role, 0) for role in unique_roles if role in role_credits)
        max_non_stacking_credit = max((non_stacking_roles.get(role, 0) for role in unique_roles if role in non_stacking_roles), default=0)
        total_role_credits = role_credits_sum + max_non_stacking_credit

        if max_credits == 0:
            max_credits = total_role_credits

        return current_credits, max_credits, removed_credits
    else:
        return 0, 0, 0  # Return a default tuple with three elements if no data is found

def update_user_credits(user_id, current_credits, removed_credits=0):
    attempts = 5
    while attempts > 0:
        try:
            with db_lock:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute('SELECT max_credits, removed_credits FROM user_credits WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                if result:
                    max_credits = result[0]
                    existing_removed_credits = result[1]
                    if current_credits > max_credits:
                        max_credits = current_credits
                    cursor.execute('UPDATE user_credits SET current_credits = ?, max_credits = ?, removed_credits = ? WHERE user_id = ?',
                                   (current_credits, max_credits, existing_removed_credits + removed_credits, user_id))
                    logging.debug(f'Updated credits for user {user_id}: current_credits = {current_credits}, max_credits = {max_credits}, removed_credits = {existing_removed_credits + removed_credits}')
                else:
                    cursor.execute('INSERT INTO user_credits (user_id, current_credits, max_credits, removed_credits) VALUES (?, ?, ?, ?)',
                                   (user_id, current_credits, current_credits, removed_credits))
                    logging.debug(f'Inserted credits for user {user_id}: current_credits = {current_credits}, removed_credits = {removed_credits}')
                connection.commit()
                cursor.close()
                connection.close()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                attempts -= 1
                time.sleep(1)
                logging.warning(f'Database is locked, retrying... {attempts} attempts left.')
            else:
                raise
    else:
        raise Exception("Failed to update user credits after multiple attempts.")

def get_user_removed_credits(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT removed_credits FROM user_credits WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result[0] if result else 0

def add_role_credits(role_name, credit_amount):
    attempts = 5
    while attempts > 0:
        try:
            with db_lock:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute('REPLACE INTO role_credits (role_name, credit_amount) VALUES (?, ?)',
                               (role_name, credit_amount))
                connection.commit()
                cursor.close()
                connection.close()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                attempts -= 1
                time.sleep(1)
                logging.warning(f'Database is locked, retrying... {attempts} attempts left.')
            else:
                raise
    else:
        raise Exception("Failed to add role credits after multiple attempts.")

def remove_role_credits(role_name):
    attempts = 5
    while attempts > 0:
        try:
            with db_lock:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute('DELETE FROM role_credits WHERE role_name = ?', (role_name,))
                connection.commit()
                cursor.close()
                connection.close()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                attempts -= 1
                time.sleep(1)
                logging.warning(f'Database is locked, retrying... {attempts} attempts left.')
            else:
                raise
    else:
        raise Exception("Failed to remove role credits after multiple attempts.")

def get_all_role_credits():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT role_name, credit_amount FROM role_credits')
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result

def create_non_stacking_roles_table():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS non_stacking_role_credits (
            role_name TEXT PRIMARY KEY,
            credit_amount INTEGER NOT NULL
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

def add_non_stacking_role_credits(role_name, credit_amount):
    attempts = 5
    while attempts > 0:
        try:
            with db_lock:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute('REPLACE INTO non_stacking_role_credits (role_name, credit_amount) VALUES (?, ?)',
                               (role_name, credit_amount))
                connection.commit()
                cursor.close()
                connection.close()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                attempts -= 1
                time.sleep(1)
                logging.warning(f'Database is locked, retrying... {attempts} attempts left.')
            else:
                raise
    else:
        raise Exception("Failed to add non-stacking role credits after multiple attempts.")

def get_all_non_stacking_role_credits():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT role_name, credit_amount FROM non_stacking_role_credits')
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result

def create_register_status_table():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS register_status (
            user_id INTEGER PRIMARY KEY
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

create_register_status_table()

def has_registered(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT user_id FROM register_status WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result is not None

def mark_as_registered(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO register_status (user_id) VALUES (?)', (user_id,))
        connection.commit()
        cursor.close()
        connection.close()

def remove_registered_status(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('DELETE FROM register_status WHERE user_id = ?', (user_id,))
        connection.commit()
        cursor.close()
        connection.close()

def initialize_roles():
    roles = [
        ("Medal of Valor", 20000),
        ("41st Service Medal", 3000),
        ("1 Year Service Medal", 3000),
        ("2 Year Service Medal", 4000),
        ("3 Year Service Medal", 6000),
        ("Cadet Master", 3000),
        ("Mythical Instructor", 3000),
        ("Legendary Instructor", 3000),
        ("Hero of The 41st", 2500),
        ("Absolutely Demolished", 2000),
        ("Legendary Ranger", 2000),
        ("Battle Hardened", 2000),
        ("Bane of Clankers", 2000),
        ("Order of Dedication", 2000),
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
        ("Lone Survivor", 5000),
        ("Exemplar", 1000),
        ("Professional Soldier", 5000),
        ("One Man Army", 1500),
        ("The Good Batch", 4000),
        ("Bred for War", 1500),
        ("Outstanding Dedication", 4000),
        ("Fireteam on Fire", 3000),
        ("First Try", 3000),
        ("Experience Outranks Everything", 8000),

        # LEVEL MEDALS
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


        # ARMY QUALIFICATIONS
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
        ("ARC Trooper", 20000),
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
        ("Sky Trooper", 5000),

        # NAVY QUALIFICATIONS
        ("Interceptor Qualification", 2000),
        ("Bomber Qualification", 2000),
        ("Ace Pilot", 3000),
        ("HERO - Dogfighter", 4000),
        ("HERO - Objective", 4000),
        ("HERO - Aerial Denial", 4000),
        ("HERO - Mobility", 4000),
        ("HERO - Support", 4000),

        # SOF medals
        ("SOF Service Medal", 3000),
        ("Special Forces Veteran", 1500),
        ("Special Forces Legend", 2000),
        ("Special Forces Myth", 2500),
        ("Unexpected Assistance", 2000),
        ("Devout Protector", 2500),
        ("Strength in Unity", 2000),
        ("Brotherhood of Steel", 2500),
        ("Brothers In Arms", 2000),
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
        ("Operation: Suppressive Shroud", 1000),
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
        ("Guardian Angel", 1000),
        ("No Mercy", 3500),
        # Regiment Medals
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
        ("Dedication is Key", 3000),
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
        ("He's going for Speed", 1000),
        ("He's Going the Distance", 1500),
        ("Basic Equipment Expert", 2000),
        ("Instructor on Fire", 1000),
        ("Praise the Maker", 1500),
        ("Instructor on Fire", 1000),
        ("FEEL THE WRATH OF THE 41ST", 1000)
    ]
    attempts = 5
    while attempts > 0:
        try:
            with db_lock:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute("BEGIN IMMEDIATE")
                cursor.executemany('REPLACE INTO role_credits (role_name, credit_amount) VALUES (?, ?)', roles)
                connection.commit()
                cursor.close()
                connection.close()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                attempts -= 1
                time.sleep(1)
                logging.warning(f'Database is locked, retrying... {attempts} attempts left.')
            else:
                raise
    else:
        raise Exception("Failed to initialize roles after multiple attempts.")

def reset_user_stats(user_id):
    attempts = 5
    while attempts > 0:
        try:
            with db_lock:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute('DELETE FROM user_credits WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM removed_credits WHERE user_id = ?', (user_id,))
                connection.commit()
                cursor.close()
                connection.close()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                attempts -= 1
                time.sleep(1)
                logging.warning(f'Database is locked, retrying... {attempts} attempts left.')
            else:
                raise
    else:
        raise Exception("Failed to reset user stats after multiple attempts.")

def initialize_non_stacking_roles():
    roles = [

        ("Clone Pilot", 1000),
        ("Clone Trooper", 1000),
        ("Flight Officer", 1500),
        ("Lance Corporal", 1500),
        ("Flight Lieutenant", 2500),
        ("Corporal", 2000),
        ("Sergeant", 2500),
        ("Flight Captain", 5000),
        ("ARC Sergeant", 5000),
        ("RC Sergeant", 5000),
        ("Sergeant Major", 5000),
        ("2nd Lieutenant", 7000),
        ("Flight Commander", 7500),
        ("ARC Lieutenant", 10000),
        ("RC Lieutenant", 10000),
        ("Lieutenant", 8000),
        ("Captain", 10000),
        ("ARC Capitain", 15000),
        ("RC Captain", 15000),
        ("Colonel", 10000),
        ("Quartermaster", 15000),
        ("Technical Commander", 20000),
        ("Major", 25000),
        ("Commander", 30000),
        ("Marshal Commander", 50000),








    ]
    attempts = 5
    while attempts > 0:
        try:
            with db_lock:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.executemany('REPLACE INTO non_stacking_role_credits (role_name, credit_amount) VALUES (?, ?)', roles)
                connection.commit()
                cursor.close()
                connection.close()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                attempts -= 1
                time.sleep(1)
                logging.warning(f'Database is locked, retrying... {attempts} attempts left.')
            else:
                raise
    else:
        raise Exception("Failed to initialize non-stacking roles after multiple attempts.")

def check_user_credits():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT user_id, current_credits, max_credits, removed_credits FROM user_credits')
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result

def create_purchases_table():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

create_purchases_table()

# Ensure that the database tables for medals and purchases exist
def create_medals_table():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_medals (
            user_id INTEGER NOT NULL,
            medal_name TEXT NOT NULL
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

create_medals_table()

def get_user_medals(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT medal_name FROM user_medals WHERE user_id = ?', (user_id,))
        medals = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return medals

def get_user_purchases(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT item_name FROM user_purchases WHERE user_id = ?', (user_id,))
        purchases = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return purchases

def update_user_roles(user_id, server_id, roles):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_roles WHERE user_id = ? AND server_id = ?', (user_id, server_id))
        cursor.executemany('INSERT INTO user_roles (user_id, server_id, role_name) VALUES (?, ?, ?)',
                           [(user_id, server_id, role.name) for role in roles])
        connection.commit()
        cursor.close()
        connection.close()


def get_user_roles_from_servers(user_id, server_ids, bot):
    user_roles = set()  # Use a set to avoid duplicate roles
    for server_id in server_ids:
        server = bot.get_guild(server_id)
        if server:
            member = server.get_member(user_id)
            if member:
                user_roles.update(role.name for role in member.roles)
                print(f"Roles from server {server_id} for user {user_id}: {[role.name for role in member.roles]}")
            else:
                print(f"User {user_id} not found in server {server_id}")
        else:
            print(f"Server {server_id} not found")
    return list(user_roles)


print(check_user_credits())

# database.py
def create_user_daily_table():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_daily (
            user_id INTEGER PRIMARY KEY,
            last_claim INTEGER,
            streak INTEGER
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

create_user_daily_table()

def get_user_daily_info(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT last_claim, streak FROM user_daily WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result

def update_user_daily_info(user_id, last_claim, streak):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('REPLACE INTO user_daily (user_id, last_claim, streak) VALUES (?, ?, ?)', (user_id, last_claim, streak))
        connection.commit()
        cursor.close()
        connection.close()

def get_top_streaks(limit=5):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT user_id, streak FROM user_daily ORDER BY streak DESC, last_claim DESC LIMIT ?', (limit,))
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result

def get_user_position(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_daily WHERE streak > (SELECT streak FROM user_daily WHERE user_id = ?) OR (streak = (SELECT streak FROM user_daily WHERE user_id = ?) AND last_claim < (SELECT last_claim FROM user_daily WHERE user_id = ?))', (user_id, user_id, user_id))
        position = cursor.fetchone()[0] + 1
        cursor.close()
        connection.close()
        return position

# Add these functions to your database.py file



def set_user_streak(user_id, streak):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE user_daily SET streak = ? WHERE user_id = ?', (streak, user_id))
        connection.commit()
        cursor.close()
        connection.close()


def create_reminder_table():
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_reminder (
            user_id INTEGER PRIMARY KEY,
            reminder_enabled BOOLEAN
        )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

def set_reminder(user_id, status):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT OR REPLACE INTO daily_reminder (user_id, reminder_enabled) VALUES (?, ?)', (user_id, status))
        connection.commit()
        cursor.close()
        connection.close()

def get_reminder_status(user_id):
    with db_lock:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT reminder_enabled FROM daily_reminder WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result[0] if result else False



# Create the tables if they do not exist and initialize roles
create_tables()
create_non_stacking_roles_table()
create_reminder_table()
initialize_roles()
initialize_non_stacking_roles()
