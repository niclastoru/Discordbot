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
        # ========== GUILD SETTINGS (prefix, etc.) ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                settings TEXT
            )
        ''')
        
        # ========== AUTORESPONDER ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS autoresponders (
                guild_id TEXT,
                trigger TEXT,
                response TEXT,
                PRIMARY KEY (guild_id, trigger)
            )
        ''')
        
        # ========== STAFF ROLES ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_roles (
                guild_id TEXT,
                role_id TEXT,
                PRIMARY KEY (guild_id, role_id)
            )
        ''')
        
        # ========== WARNINGS ==========
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
        
        # ========== JAIL SYSTEM ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jail_settings (
                guild_id TEXT PRIMARY KEY,
                jail_role_id TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jailed_users (
                guild_id TEXT,
                user_id TEXT,
                reason TEXT,
                jailed_at TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        # ========== WORD FILTER ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wordfilter (
                guild_id TEXT,
                word TEXT,
                PRIMARY KEY (guild_id, word)
            )
        ''')
        
        # ========== REMINDERS ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                channel_id TEXT,
                message TEXT,
                remind_time TEXT
            )
        ''')
        
        # ========== REACTION ROLES ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reaction_roles (
                guild_id TEXT,
                message_id TEXT,
                emoji TEXT,
                role_id TEXT,
                PRIMARY KEY (guild_id, message_id, emoji)
            )
        ''')
        
        # ========== LEVELING ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                guild_id TEXT,
                user_id TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        # ========== MARRIAGES (für fun cog) ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS marriages (
                guild_id TEXT,
                user_id TEXT,
                partner_id TEXT,
                married_at TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        # ========== STICKY MESSAGES ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sticky_messages (
                guild_id TEXT,
                channel_id TEXT,
                message_id TEXT,
                content TEXT,
                PRIMARY KEY (guild_id, channel_id)
            )
        ''')
        
        # ========== DISABLED COMMANDS ==========
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS disabled_commands (
                guild_id TEXT,
                command_name TEXT,
                PRIMARY KEY (guild_id, command_name)
            )
        ''')
        
        self.conn.commit()
        print("✅ Alle Datenbank-Tabellen wurden erstellt")

    # ========== GUILD SETTINGS ==========
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

    # ========== AUTORESPONDER ==========
    def add_autoresponder(self, guild_id, trigger, response):
        self.cursor.execute(
            "INSERT OR REPLACE INTO autoresponders (guild_id, trigger, response) VALUES (?, ?, ?)",
            (str(guild_id), trigger.lower(), response)
        )
        self.conn.commit()
    
    def remove_autoresponder(self, guild_id, trigger):
        self.cursor.execute(
            "DELETE FROM autoresponders WHERE guild_id = ? AND trigger = ?",
            (str(guild_id), trigger.lower())
        )
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_autoresponders(self, guild_id):
        self.cursor.execute(
            "SELECT trigger, response FROM autoresponders WHERE guild_id = ?",
            (str(guild_id),)
        )
        return {row[0]: row[1] for row in self.cursor.fetchall()}
    
    def get_all_autoresponders(self):
        self.cursor.execute("SELECT guild_id, trigger, response FROM autoresponders")
        return self.cursor.fetchall()

    # ========== STAFF ROLES ==========
    def add_staff_role(self, guild_id, role_id):
        self.cursor.execute(
            "INSERT OR IGNORE INTO staff_roles (guild_id, role_id) VALUES (?, ?)",
            (str(guild_id), str(role_id))
        )
        self.conn.commit()
    
    def remove_staff_role(self, guild_id, role_id):
        self.cursor.execute(
            "DELETE FROM staff_roles WHERE guild_id = ? AND role_id = ?",
            (str(guild_id), str(role_id))
        )
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_staff_roles(self, guild_id):
        self.cursor.execute(
            "SELECT role_id FROM staff_roles WHERE guild_id = ?",
            (str(guild_id),)
        )
        return [row[0] for row in self.cursor.fetchall()]

    # ========== WARNINGS ==========
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

    # ========== JAIL SYSTEM ==========
    def set_jail_role(self, guild_id, role_id):
        self.cursor.execute(
            "INSERT OR REPLACE INTO jail_settings (guild_id, jail_role_id) VALUES (?, ?)",
            (str(guild_id), str(role_id))
        )
        self.conn.commit()
    
    def get_jail_role(self, guild_id):
        self.cursor.execute("SELECT jail_role_id FROM jail_settings WHERE guild_id = ?", (str(guild_id),))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def add_jailed_user(self, guild_id, user_id, reason):
        self.cursor.execute(
            "INSERT OR REPLACE INTO jailed_users (guild_id, user_id, reason, jailed_at) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(user_id), reason, str(datetime.utcnow()))
        )
        self.conn.commit()
    
    def remove_jailed_user(self, guild_id, user_id):
        self.cursor.execute(
            "DELETE FROM jailed_users WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        self.conn.commit()
    
    def get_jailed_users(self, guild_id):
        self.cursor.execute("SELECT user_id FROM jailed_users WHERE guild_id = ?", (str(guild_id),))
        return [row[0] for row in self.cursor.fetchall()]

    # ========== WORD FILTER ==========
    def add_filtered_word(self, guild_id, word):
        self.cursor.execute(
            "INSERT OR IGNORE INTO wordfilter (guild_id, word) VALUES (?, ?)",
            (str(guild_id), word.lower())
        )
        self.conn.commit()
    
    def remove_filtered_word(self, guild_id, word):
        self.cursor.execute(
            "DELETE FROM wordfilter WHERE guild_id = ? AND word = ?",
            (str(guild_id), word.lower())
        )
        self.conn.commit()
    
    def get_filtered_words(self, guild_id):
        self.cursor.execute("SELECT word FROM wordfilter WHERE guild_id = ?", (str(guild_id),))
        return [row[0] for row in self.cursor.fetchall()]

    # ========== REMINDERS ==========
    def add_reminder(self, user_id, channel_id, message, remind_time):
        self.cursor.execute(
            "INSERT INTO reminders (user_id, channel_id, message, remind_time) VALUES (?, ?, ?, ?)",
            (str(user_id), str(channel_id), message, remind_time.isoformat())
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_reminders(self, user_id):
        self.cursor.execute(
            "SELECT id, user_id, channel_id, message, remind_time FROM reminders WHERE user_id = ?",
            (str(user_id),)
        )
        return self.cursor.fetchall()
    
    def delete_reminder(self, reminder_id):
        self.cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        self.conn.commit()

    # ========== REACTION ROLES ==========
    def add_reaction_role(self, guild_id, message_id, emoji, role_id):
        self.cursor.execute(
            "INSERT OR REPLACE INTO reaction_roles (guild_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(message_id), str(emoji), str(role_id))
        )
        self.conn.commit()
    
    def remove_reaction_role(self, guild_id, message_id, emoji):
        self.cursor.execute(
            "DELETE FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (str(guild_id), str(message_id), str(emoji))
        )
        self.conn.commit()
    
    def get_reaction_roles(self, guild_id, message_id):
        self.cursor.execute(
            "SELECT emoji, role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ?",
            (str(guild_id), str(message_id))
        )
        return {row[0]: row[1] for row in self.cursor.fetchall()}
    
    def get_all_reaction_roles(self, guild_id):
        self.cursor.execute(
            "SELECT message_id, emoji, role_id FROM reaction_roles WHERE guild_id = ?",
            (str(guild_id),)
        )
        result = {}
        for row in self.cursor.fetchall():
            if row[0] not in result:
                result[row[0]] = {}
            result[row[0]][row[1]] = row[2]
        return result

    # ========== LEVELING ==========
    def get_user_xp(self, guild_id, user_id):
        self.cursor.execute(
            "SELECT xp, level FROM levels WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        row = self.cursor.fetchone()
        return {"xp": row[0], "level": row[1]} if row else {"xp": 0, "level": 0}
    
    def set_user_xp(self, guild_id, user_id, xp, level):
        self.cursor.execute(
            "INSERT OR REPLACE INTO levels (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(user_id), xp, level)
        )
        self.conn.commit()
    
    def update_user_xp(self, guild_id, user_id, xp):
        self.cursor.execute(
            "UPDATE levels SET xp = ? WHERE guild_id = ? AND user_id = ?",
            (xp, str(guild_id), str(user_id))
        )
        self.conn.commit()
    
    def get_level_leaderboard(self, guild_id, limit=100):
        self.cursor.execute(
            "SELECT user_id, xp, level FROM levels WHERE guild_id = ? ORDER BY xp DESC LIMIT ?",
            (str(guild_id), limit)
        )
        return self.cursor.fetchall()

    # ========== MARRIAGES ==========
    def marry(self, guild_id, user_id, partner_id):
        married_at = str(datetime.utcnow())
        self.cursor.execute(
            "INSERT OR REPLACE INTO marriages (guild_id, user_id, partner_id, married_at) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(user_id), str(partner_id), married_at)
        )
        self.cursor.execute(
            "INSERT OR REPLACE INTO marriages (guild_id, user_id, partner_id, married_at) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(partner_id), str(user_id), married_at)
        )
        self.conn.commit()
    
    def divorce(self, guild_id, user_id):
        self.cursor.execute(
            "DELETE FROM marriages WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        self.conn.commit()
    
    def get_married(self, guild_id, user_id):
        self.cursor.execute(
            "SELECT partner_id FROM marriages WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    # ========== STICKY MESSAGES ==========
    def set_sticky_message(self, guild_id, channel_id, message_id, content):
        self.cursor.execute(
            "INSERT OR REPLACE INTO sticky_messages (guild_id, channel_id, message_id, content) VALUES (?, ?, ?, ?)",
            (str(guild_id), str(channel_id), str(message_id), content)
        )
        self.conn.commit()
    
    def remove_sticky_message(self, guild_id, channel_id):
        self.cursor.execute(
            "DELETE FROM sticky_messages WHERE guild_id = ? AND channel_id = ?",
            (str(guild_id), str(channel_id))
        )
        self.conn.commit()
    
    def get_sticky_message(self, guild_id, channel_id):
        self.cursor.execute(
            "SELECT message_id, content FROM sticky_messages WHERE guild_id = ? AND channel_id = ?",
            (str(guild_id), str(channel_id))
        )
        row = self.cursor.fetchone()
        return {"message_id": row[0], "content": row[1]} if row else None

    # ========== DISABLED COMMANDS ==========
    def disable_command(self, guild_id, command_name):
        self.cursor.execute(
            "INSERT OR IGNORE INTO disabled_commands (guild_id, command_name) VALUES (?, ?)",
            (str(guild_id), command_name)
        )
        self.conn.commit()
    
    def enable_command(self, guild_id, command_name):
        self.cursor.execute(
            "DELETE FROM disabled_commands WHERE guild_id = ? AND command_name = ?",
            (str(guild_id), command_name)
        )
        self.conn.commit()
    
    def is_command_disabled(self, guild_id, command_name):
        self.cursor.execute(
            "SELECT 1 FROM disabled_commands WHERE guild_id = ? AND command_name = ?",
            (str(guild_id), command_name)
        )
        return self.cursor.fetchone() is not None
    
    def get_disabled_commands(self, guild_id):
        self.cursor.execute(
            "SELECT command_name FROM disabled_commands WHERE guild_id = ?",
            (str(guild_id),)
        )
        return [row[0] for row in self.cursor.fetchall()]

    # ========== CLOSE ==========
    def close(self):
        self.conn.close()

# Globale Datenbankinstanz
db = Database()
