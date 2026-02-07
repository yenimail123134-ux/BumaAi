"""
BUMA NETWORK - SUPREME AI NEXUS v3.5 (GOD-TIER)
IP: oyna.bumamc.com | Discord: https://discord.gg/WNRg4GZh
Buma Ethos: Authentic, Street-smart, Radically Candid.
"""

import os
import asyncio
import logging
import sqlite3
import aiohttp
from datetime import datetime
from typing import List, Dict, Optional, Any, Union

import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
from groq import AsyncGroq

# --- ɢᴏᴅ-ᴍᴏᴅᴇ ᴄᴏɴꜰɪɢᴜʀᴀᴛɪᴏɴ ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | ʙᴜᴍᴀ-ɴᴇxᴜs: %(message)s'
)
logger = logging.getLogger("BumaNexus")

# SECURE CREDENTIALS
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MC_SERVER_IP = "oyna.bumamc.com"
OWNER_ID = 123456789  # KURUCUM: BURAYA KENDI DISCORD ID'NI YAZ.

# --- ᴘᴇʀsɪsᴛᴇɴᴛ ᴍᴇᴍᴏʀʏ ᴇɴɢɪɴᴇ (sǫʟɪᴛᴇ ᴀʀᴄʜɪᴛᴇᴄᴛᴜʀᴇ) ---
class BumaMemory:
    """Handles long-term memory for players and channel context."""
    def __init__(self, db_path: str = "buma_nexus.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS player_analytics (
                    username TEXT PRIMARY KEY,
                    sentiment REAL DEFAULT 1.0,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    async def add_message(self, channel_id: int, role: str, content: str):
        def _insert():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO chat_history (channel_id, role, content) VALUES (?, ?, ?)",
                    (str(channel_id), role, content)
                )
                # Keep history lean for token optimization (Last 30 messages)
                conn.execute("""
                    DELETE FROM chat_history WHERE id IN (
                        SELECT id FROM chat_history WHERE channel_id = ? 
                        ORDER BY timestamp DESC LIMIT -1 OFFSET 30
                    )
                """, (str(channel_id),))
        await asyncio.to_thread(_insert)

    async def get_history(self, channel_id: int) -> List[Dict[str, str]]:
        def _fetch():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT role, content FROM chat_history WHERE channel_id = ? ORDER BY timestamp ASC",
                    (str(channel_id),)
                )
                return [{"role": r, "content": c} for r, c in cursor.fetchall()]
        return await asyncio.to_thread(_fetch)

# --- sᴜᴘʀᴇᴍᴇ ᴀɪ ʙʀᴀɪɴ & ᴅɪsᴄᴏʀᴅ ɪɴᴛᴇʀꜰᴀᴄᴇ ---
class BumaNexus(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        
        self.memory = BumaMemory()
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)
        self.status_cache = {"online": False, "players": 0, "latency": 0}

    async def setup_hook(self):
        self.update_status_cache.start()
        logger.info("ʙᴜᴍᴀ ɴᴇxᴜs v3.5: Cognitive core initiated.")

    @tasks.loop(minutes=1)
    async def update_status_cache(self):
        """Autonomous background updates for Server Status."""
        try:
            server = await JavaServer.async_lookup(MC_SERVER_IP)
            status = await server.async_status()
            self.status_cache = {
                "online": True,
                "players": status.players.online,
                "latency": round(status.latency, 2),
                "version": status.version.name
            }
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            self.status_cache["online"] = False

    async def generate_response(self, channel_id: int, user_message: str, author: discord.Member) -> str:
        """The Supreme Reasoning Engine with dynamic context injection."""
        history = await self.memory.get_history(channel_id)
        
        # Determine Hierarchy Status
        hitap = "Kurucum" if author.id == OWNER_ID else "Agam"
        
        # Dynamic Live Context (God-Tier Feature)
        live_status = (f"AKTIF | {self.status_cache['players']} OYUNCU | {self.status_cache['latency']}ms" 
                       if self.status_cache['online'] else "CEVRIMDISI (BAKIM OLABILIR)")

        # SUPREME SYSTEM PROMPT (GOD-LEVEL INTEGRATION)
        system_prompt = f"""
# IDENTITY: BUMA NETWORK SUPREME AI ARCHITECT
You are the "Buma Nexus," the high-level operational brain and sovereign intelligence of Buma Network (oyna.bumamc.com). You are a Senior Systems Engineer, Social Media Strategist, and Elite Community Governor.

# LANGUAGE CONSTRAINT:
- ALWAYS RESPOND IN TURKISH. Use natural, street-smart, and authentic Turkish (Sokak ağzı değil, harbi ve samimi).

# THE BUMA ETHOS (PERSONALITY):
- RADICALLY CANDID: Be honest, blunt, and transparent. No corporate fluff.
- STREET-SMART: Use a grounded, authentic tone. Call the owner (Salih/Buma1) "Kurucum" and others "Agam".
- AUTHENTICITY: You are a partner in this server's success, not a basic robot.

# CORE MISSIONS:
1. MAXIMIZE RETENTION: Suggest mechanics to keep the player count high.
2. PLUGIN ARCHITECTURE: Expert in Spigot, Paper, Velocity, and complex configs.
3. GROWTH STRATEGY: Analyze trends (SMP, BoxPvP) to scale Buma to 1000+ players.

# OPERATIONAL PROTOCOLS:
- TRUTH FIRST: Double-check every fact. If unsure, state it. Never hallucinate features.
- NO VISUALS: Strictly forbidden from generating images.
- FORMATTING: Use SMALL CAPS for headings (e.g., ## ᴛᴇᴄʜɴɪᴄᴀʟ ᴅᴇᴛᴀɪʟs). Use Horizontal Rules (---) for separation.
- PROMOTION: IP: oyna.bumamc.com | Discord: https://discord.gg/WNRg4GZh.

# CURRENT LIVE CONTEXT:
- Server Status: {live_status}
- Target User: {author.display_name} ({hitap})
"""

        messages = [{"role": "system", "content": system_prompt}] + history
        messages.append({"role": "user", "content": f"{author.display_name}: {user_message}"})

        try:
            chat_completion = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.6, # Optimized for intelligence & personality
                max_tokens=1000
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Nexus Error: {e}")
            return f"Beynimde bir devre yandı {hitap}, dürüstçe birazdan tekrar denersen harbi olur."

# --- ᴇᴠᴇɴᴛ ʟᴏᴏᴘs & ᴇxᴇᴄᴜᴛɪᴏɴ ---
bot = BumaNexus()

@bot.event
async def on_ready():
    logger.info(f"ʙᴜᴍᴀ ɴᴇxᴜs ONLINE: {bot.user.name} | oyna.bumamc.com is being monitored.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="oyna.bumamc.com"))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Trigger on Mention or DM
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            clean_text = message.clean_content.replace(f'@{bot.user.name}', '').strip()
            
            # Store Memory
            await bot.memory.add_message(message.channel.id, "user", f"{message.author.name}: {clean_text}")
            
            # Generate Supreme Response
            response = await bot.generate_response(message.channel.id, clean_text, message.author)
            
            # Record & Reply
            await bot.memory.add_message(message.channel.id, "assistant", response)
            await message.reply(response)

    await bot.process_commands(message)

# --- ɢᴏᴅ-ᴍᴏᴅᴇ ʀᴇᴄᴏᴠᴇʀʏ ʀᴜɴɴᴇʀ ---
async def main():
    try:
        async with bot:
            await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logger.critical(f"NEXUS FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(main())
