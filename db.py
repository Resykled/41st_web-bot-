# db.py
import sqlite3
import os
import json
import random

DB_NAME = "campaign.db"

def init_db():
    """
    Initializes the database (SQLite) and creates tables if they do not exist.
    Also attempts to add new columns if needed.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1) Tabelle anlegen (falls noch nicht existiert)
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY,
            grid_json TEXT,
            friendly_x INTEGER,
            friendly_y INTEGER,
            enemy_x INTEGER,
            enemy_y INTEGER,
            wins INTEGER,
            losses INTEGER,
            last_move_direction TEXT,
            special_event_active INTEGER,
            special_event_end_time TEXT,
            event_name TEXT,
            -- Neu: Hier fügen wir eine Spalte für HQ-Event-Daten hinzu
            hq_event_json TEXT
        )
    """)

    # 2) Versuchen, hq_event_json nachträglich anzulegen, falls sie in einer älteren DB noch fehlt
    try:
        c.execute("ALTER TABLE game_state ADD COLUMN hq_event_json TEXT")
    except sqlite3.OperationalError:
        # Spalte existiert bereits - alles gut
        pass

    # 3) Prüfen, ob schon ein Datensatz existiert
    c.execute("SELECT COUNT(*) FROM game_state")
    count = c.fetchone()[0]

    if count == 0:
        # Erster Datensatz -> Standardzustand
        grid = [[{"state": "hidden"} for _ in range(10)] for _ in range(10)]
        friendly_x, friendly_y = 0, 0
        enemy_x, enemy_y = 9, 9

        c.execute("""
            INSERT INTO game_state 
            (id, grid_json, friendly_x, friendly_y, enemy_x, enemy_y, 
             wins, losses, last_move_direction, special_event_active, 
             special_event_end_time, event_name, hq_event_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,
            json.dumps(grid),
            friendly_x,
            friendly_y,
            enemy_x,
            enemy_y,
            0,  # wins
            0,  # losses
            "none",  # last_move_direction
            0,       # special_event_active
            "",      # special_event_end_time
            "",      # event_name
            json.dumps({})  # leeres HQ-Event
        ))
        conn.commit()

    conn.close()

def get_game_state():
    """
    Retrieves the current game state from the database.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM game_state WHERE id = 1")
    row = c.fetchone()
    conn.close()

    if row:
        # row schema nach obigem CREATE:
        # 0: id
        # 1: grid_json
        # 2: friendly_x
        # 3: friendly_y
        # 4: enemy_x
        # 5: enemy_y
        # 6: wins
        # 7: losses
        # 8: last_move_direction
        # 9: special_event_active
        # 10: special_event_end_time
        # 11: event_name
        # 12: hq_event_json (neu)
        hq_event_raw = row[12] if row[12] else "{}"
        try:
            hq_event = json.loads(hq_event_raw)
        except:
            hq_event = {}

        return {
            "grid": json.loads(row[1]),
            "friendly_x": row[2],
            "friendly_y": row[3],
            "enemy_x": row[4],
            "enemy_y": row[5],
            "wins": row[6],
            "losses": row[7],
            "last_move_direction": row[8],
            "special_event_active": bool(row[9]),
            "special_event_end_time": row[10],
            "event_name": row[11],
            "hq_event": hq_event  # das gesamte Dictionary für HQ-Events
        }
    else:
        return None

def update_game_state(state_dict):
    print(f"[DEBUG] update_game_state: friendly=({state_dict['friendly_x']},{state_dict['friendly_y']}) "
          f"enemy=({state_dict['enemy_x']},{state_dict['enemy_y']}), "
          f"wins={state_dict['wins']}, losses={state_dict['losses']}")
    """
    Persists the entire game state dictionary back into the database.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Alles, was wir in state_dict haben, wieder zurückschreiben
    c.execute("""
        UPDATE game_state
        SET grid_json = ?,
            friendly_x = ?,
            friendly_y = ?,
            enemy_x = ?,
            enemy_y = ?,
            wins = ?,
            losses = ?,
            last_move_direction = ?,
            special_event_active = ?,
            special_event_end_time = ?,
            event_name = ?,
            hq_event_json = ?
        WHERE id = 1
    """, (
        json.dumps(state_dict["grid"]),
        state_dict["friendly_x"],
        state_dict["friendly_y"],
        state_dict["enemy_x"],
        state_dict["enemy_y"],
        state_dict["wins"],
        state_dict["losses"],
        state_dict["last_move_direction"],
        1 if state_dict["special_event_active"] else 0,
        state_dict["special_event_end_time"],
        state_dict["event_name"],
        json.dumps(state_dict["hq_event"])  # hq_event als JSON
    ))
    conn.commit()
    conn.close()

def reset_db():
    """
    Wipes the existing data and reinitializes the database.
    """
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()

def place_objectives(num_friendly=10, num_enemy=10):
    """
    Randomly place friendly and enemy objectives on the grid.
    """
    state = get_game_state()
    grid = state["grid"]

    placed_friendly = 0
    placed_enemy = 0
    size = 10

    while placed_friendly < num_friendly or placed_enemy < num_enemy:
        x, y = random.randint(0, size - 1), random.randint(0, size - 1)
        if grid[x][y]["state"] == "hidden":  # Nur auf versteckten Feldern platzieren
            if placed_friendly < num_friendly:
                grid[x][y]["state"] = "friendly_objective"
                placed_friendly += 1
            elif placed_enemy < num_enemy:
                grid[x][y]["state"] = "enemy_objective"
                placed_enemy += 1

    state["grid"] = grid
    update_game_state(state)

def render_map(grid):
    """
    Creates a text-based representation of the map using emojis.
    """
    symbols = {
        "hidden": "⬜",
        "visited": "⬛",
        "friendly_objective": "🟩",
        "enemy_objective": "🟥",
        # optional: falls du weitere States hast (z.B. erobert/verloren), hier ergänzen:
        # "friendly_objective_captured": "🟦",
        # "friendly_objective_lost": "🟫",
        # etc.
    }
    rows = []
    for row in grid:
        row_str = "".join(symbols.get(cell["state"], "⬜") for cell in row)
        rows.append(row_str)
    return "\n".join(rows)
