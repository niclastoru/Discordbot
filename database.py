import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name="bot_data.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                auto_responders TEXT,
                reaction_roles TEXT,
                disabled_commands TEXT,
                settings TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                user_id TEXT,
                reason TEXT,
                moderator TEXT,
                date TEXT
            )
        ''')
        
        self.conn.commit()
        print("✅ Datenbank Tabellen erstellt")

    def get_guild_settings(self, guild_id):
        guild_id = str(guild_id)
        self.cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        row = self.cursor.fetchone()
        
        if row:
            return {
                "auto_responders": json.loads(row[1]) if row[1] else {},
                "reaction_roles": json.loads(row[2]) if row[2] else {},
                "disabled_commands": json.loads(row[3]) if row[3] else [],
                "settings": json.loads(row[4]) if row[4] else {}
            }
        else:
            default = {
                "auto_responders": {},
                "reaction_roles": {},
                "disabled_commands": [],
                "settings": {}
            }
            self.cursor.execute(
                "INSERT INTO guild_settings VALUES (?, ?, ?, ?, ?)",
                (guild_id, json.dumps(default["auto_responders"]), 
                 json.dumps(default["reaction_roles"]), 
                 json.dumps(default["disabled_commands"]),
                 json.dumps(default["settings"]))
            )
            self.conn.commit()
            return default

    def update_guild_settings(self, guild_id, key, value):
        settings = self.get_guild_settings(guild_id)
        settings[key] = value
        self.cursor.execute(
            """UPDATE guild_settings 
               SET auto_responders = ?, reaction_roles = ?, disabled_commands = ?, settings = ? 
               WHERE guild_id = ?""",
            (json.dumps(settings["auto_responders"]), 
             json.dumps(settings["reaction_roles"]),
             json.dumps(settings["disabled_commands"]),
             json.dumps(settings["settings"]), 
             str(guild_id))
        )
        self.conn.commit()

    def add_warning(self, guild_id, user_id, reason, moderator):
        self.cursor.execute(
            "INSERT INTO warnings (guild_id, user_id, reason, moderator, date) VALUES (?, ?, ?, ?, ?)",
            (str(guild_id), str(user_id), reason, str(moderator), str(datetime.utcnow()))
        )
        self.conn.commit()

    def get_warnings(self, guild_id, user_id):
        self.cursor.execute(
            "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

db = Database()
