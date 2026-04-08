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
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        """Create all necessary tables for all cogs"""
        
        # Guild Settings (for admin, settings, servers cogs)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                auto_responders TEXT,
                reaction_roles TEXT,
                sticky_messages TEXT,
                disabled_commands TEXT,
                settings TEXT
            )
        ''')
        
        # Warnings (for moderation cog)
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
        
        # Jail System (for moderation cog)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jailed_users (
                guild_id TEXT,
                user_id TEXT,
                reason TEXT,
                jailed_at TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        # Jail Role Settings (for moderation cog)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jail_settings (
                guild_id TEXT PRIMARY KEY,
                jail_role_id TEXT
            )
        ''')
        
        # Word Filter (for moderation cog)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wordfilter (
                guild_id TEXT,
                word TEXT,
                PRIMARY KEY (guild_id, word)
            )
        ''')
        
        # Reminders (for utility cog)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                channel_id TEXT,
                message TEXT,
                remind_time TEXT
            )
        ''')
        
        # Protection Settings (for admin cog)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS protection_settings (
                guild_id TEXT PRIMARY KEY,
                antinuke INTEGER DEFAULT 0,
                antiraid INTEGER DEFAULT 0
            )
        ''')
        
        # Leveling System (for leveling cog)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                guild_id TEXT,
                user_id TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        # Global Settings (for leveling marriages etc.)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        self.conn.commit()
        print("✅ Alle Datenbank Tabellen wurden erstellt")

    # ========== GUILD SETTINGS ==========
    
    def get_guild_settings(self, guild_id):
        """Get all settings for a guild"""
        guild_id = str(guild_id)
        self.cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        row = self.cursor.fetchone()
        
        if row:
            return {
                "auto_responders": json.loads(row[1]) if row[1] else {},
                "reaction_roles": json.loads(row[2]) if row[2] else {},
                "sticky_messages": json.loads(row[3]) if row[3] else {},
                "disabled_commands": json.loads(row[4]) if row[4] else [],
                "settings": json.loads(row[5]) if row[5] else {}
            }
        else:
            # Default settings
            default = {
                "auto_responders": {},
                "reaction_roles": {},
                "sticky_messages": {},
                "disabled_commands": [],
                "settings": {}
            }
            self.cursor.execute(
                "INSERT INTO guild_settings VALUES (?, ?, ?, ?, ?, ?)",
                (guild_id, json.dumps(default["auto_responders"]), 
                 json.dumps(default["reaction_roles"]), json.dumps(default["sticky_messages"]),
                 json.dumps(default["disabled_commands"]), json.dumps(default["settings"]))
            )
            self.conn.commit()
            return default
    
    def update_guild_settings(self, guild_id, key, value):
        """Update a specific setting for a guild"""
        settings = self.get_guild_settings(guild_id)
        settings[key] = value
        
        self.cursor.execute(
            """UPDATE guild_settings 
               SET auto_responders = ?, reaction_roles = ?, sticky_messages = ?, 
                   disabled_commands = ?, settings = ? 
               WHERE guild_id = ?""",
            (json.dumps(settings["auto_responders"]), json.dumps(settings["reaction_roles"]),
             json.dumps(settings["sticky_messages"]), json.dumps(settings["disabled_commands"]),
             json.dumps(settings["settings"]), str(guild_id))
        )
        self.conn.commit()

    # ========== WARNINGS ==========
    
    def add_warning(self, guild_id, user_id, reason, moderator):
        """Add a warning for a user"""
        self.cursor.execute(
            "INSERT INTO warnings (guild_id, user_id, reason, moderator, date) VALUES (?, ?, ?, ?, ?)",
            (str(guild_id), str(user_id), reason, str(moderator), str(datetime.utcnow()))
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_warnings(self, guild_id, user_id):
        """Get all warnings for a user"""
        self.cursor.execute(
            "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY date DESC",
            (str(guild_id), str(user_id))
        )
        return self.cursor.fetchall()
    
    def clear_warnings(self, guild_id, user_id):
        """Clear all warnings for a user"""
        self.cursor.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        self.conn.commit()

    # ========== JAIL SYSTEM ==========
    
    def set_jail_role(self, guild_id, role_id):
        """Set the jail role for a guild"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO jail_settings (guild_id, jail_role_id) VALUES (?, ?)",
            (str(guild_id), str(role_id))
        )
        self.conn.commit()
    
    def get_jail_role(self, guild_id):
        """Get the jail role for a guild"""
        self.cursor.execute(
            "SELECT jail_role_id FROM jail_settings WHERE guild_id = ?",
            (str(guild_id),)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def add_jailed_user(self, guild_id, user_id, reason):
        """Add a user to jail list"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO jailed_users (guild_id, user_id, reason, jailed_at) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(user_id), reason, str(datetime.utcnow()))
        )
        self.conn.commit()
    
    def remove_jailed_user(self, guild_id, user_id):
        """Remove a user from jail list"""
        self.cursor.execute(
            "DELETE FROM jailed_users WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        self.conn.commit()
    
    def get_jailed_users(self, guild_id):
        """Get all jailed users for a guild"""
        self.cursor.execute(
            "SELECT user_id FROM jailed_users WHERE guild_id = ?",
            (str(guild_id),)
        )
        return [row[0] for row in self.cursor.fetchall()]

    # ========== WORD FILTER ==========
    
    def add_filtered_word(self, guild_id, word):
        """Add a word to filter list"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO wordfilter (guild_id, word) VALUES (?, ?)",
            (str(guild_id), word.lower())
        )
        self.conn.commit()
    
    def remove_filtered_word(self, guild_id, word):
        """Remove a word from filter list"""
        self.cursor.execute(
            "DELETE FROM wordfilter WHERE guild_id = ? AND word = ?",
            (str(guild_id), word.lower())
        )
        self.conn.commit()
    
    def get_filtered_words(self, guild_id):
        """Get all filtered words for a guild"""
        self.cursor.execute(
            "SELECT word FROM wordfilter WHERE guild_id = ?",
            (str(guild_id),)
        )
        return [row[0] for row in self.cursor.fetchall()]

    # ========== REMINDERS ==========
    
    def add_reminder(self, user_id, channel_id, message, remind_time):
        """Add a reminder"""
        self.cursor.execute(
            "INSERT INTO reminders (user_id, channel_id, message, remind_time) VALUES (?, ?, ?, ?)",
            (str(user_id), str(channel_id), message, remind_time.isoformat())
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_reminders(self, user_id):
        """Get all reminders for a user"""
        self.cursor.execute(
            "SELECT id, user_id, channel_id, message, remind_time FROM reminders WHERE user_id = ?",
            (str(user_id),)
        )
        return self.cursor.fetchall()
    
    def delete_reminder(self, reminder_id):
        """Delete a reminder"""
        self.cursor.execute(
            "DELETE FROM reminders WHERE id = ?",
            (reminder_id,)
        )
        self.conn.commit()
    
    def get_due_reminders(self):
        """Get all reminders that are due"""
        now = datetime.utcnow().isoformat()
        self.cursor.execute(
            "SELECT * FROM reminders WHERE remind_time <= ?",
            (now,)
        )
        return self.cursor.fetchall()

    # ========== PROTECTION (ANTI-NUKE/ANTI-RAID) ==========
    
    def set_antinuke(self, guild_id, enabled):
        """Enable/disable anti-nuke"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO protection_settings (guild_id, antinuke) VALUES (?, ?)",
            (str(guild_id), 1 if enabled else 0)
        )
        self.conn.commit()
    
    def get_antinuke(self, guild_id):
        """Get anti-nuke status"""
        self.cursor.execute(
            "SELECT antinuke FROM protection_settings WHERE guild_id = ?",
            (str(guild_id),)
        )
        row = self.cursor.fetchone()
        return row[0] == 1 if row else False
    
    def set_antiraid(self, guild_id, enabled):
        """Enable/disable anti-raid"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO protection_settings (guild_id, antiraid) VALUES (?, ?)",
            (str(guild_id), 1 if enabled else 0)
        )
        self.conn.commit()
    
    def get_antiraid(self, guild_id):
        """Get anti-raid status"""
        self.cursor.execute(
            "SELECT antiraid FROM protection_settings WHERE guild_id = ?",
            (str(guild_id),)
        )
        row = self.cursor.fetchone()
        return row[0] == 1 if row else False

    # ========== LEVELING SYSTEM ==========
    
    def get_user_xp(self, guild_id, user_id):
        """Get XP and level for a user"""
        self.cursor.execute(
            "SELECT xp, level FROM levels WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        row = self.cursor.fetchone()
        if row:
            return {"xp": row[0], "level": row[1]}
        return {"xp": 0, "level": 0}
    
    def set_user_xp(self, guild_id, user_id, xp, level):
        """Set XP and level for a user"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO levels (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(user_id), xp, level)
        )
        self.conn.commit()
    
    def update_user_xp(self, guild_id, user_id, xp):
        """Update XP for a user"""
        self.cursor.execute(
            "UPDATE levels SET xp = ? WHERE guild_id = ? AND user_id = ?",
            (xp, str(guild_id), str(user_id))
        )
        self.conn.commit()
    
    def get_level_leaderboard(self, guild_id, limit=100):
        """Get XP leaderboard for a guild"""
        self.cursor.execute(
            "SELECT user_id, xp, level FROM levels WHERE guild_id = ? ORDER BY xp DESC LIMIT ?",
            (str(guild_id), limit)
        )
        return self.cursor.fetchall()
    
    def delete_user_levels(self, guild_id, user_id):
        """Delete a user from leveling system"""
        self.cursor.execute(
            "DELETE FROM levels WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        self.conn.commit()
    
    def delete_guild_levels(self, guild_id):
        """Delete all leveling data for a guild"""
        self.cursor.execute(
            "DELETE FROM levels WHERE guild_id = ?",
            (str(guild_id),)
        )
        self.conn.commit()
        return self.cursor.rowcount

    # ========== GLOBAL SETTINGS ==========
    
    def get_global_setting(self, key):
        """Get a global setting value"""
        self.cursor.execute("SELECT value FROM global_settings WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None
    
    def set_global_setting(self, key, value):
        """Set a global setting value"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO global_settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value))
        )
        self.conn.commit()

    # ========== UTILITY ==========
    
    def close(self):
        """Close database connection"""
        self.conn.close()

# Globale Datenbankinstanz
db = Database()
