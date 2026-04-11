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
        # Guild Settings (für settings.py)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                settings TEXT
            )
        ''')
        
        # Warnings (für moderation.py)
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
        print("✅ Datenbank-Tabellen erstellt")

    # ========== SETTINGS (für settings.py) ==========
    def get_prefix(self, guild_id):
        self.cursor.execute("SELECT prefix FROM guild_settings WHERE guild_id = ?", (str(guild_id),))
        row = self.cursor.fetchone()
        return row[0] if row else "!"
    
    def set_prefix(self, guild_id, prefix):
        self.cursor.execute(
            "INSERT OR REPLACE INTO guild_settings (guild_id, prefix, settings) VALUES (?, ?, ?)",
            (str(guild_id), prefix, "{}")
        )
        self.conn.commit()

    # ========== WARNINGS (für moderation.py) ==========
    def add_warning(self, guild_id, user_id, reason, moderator):
        self.cursor.execute(
            "INSERT INTO warnings (guild_id, user_id, reason, moderator, date) VALUES (?, ?, ?, ?, ?)",
            (str(guild_id), str(user_id), reason, str(moderator), str(datetime.utcnow()))
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_warnings(self, guild_id, user_id):
        self.cursor.execute(
            "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY date DESC",
            (str(guild_id), str(user_id))
        )
        return self.cursor.fetchall()

    def clear_warnings(self, guild_id, user_id):
        self.cursor.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

# Globale Datenbankinstanz
db = Database()
