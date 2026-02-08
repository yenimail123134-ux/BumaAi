import os
import asyncio
import logging
import sqlite3
import nextcord
import socket
import re
from nextcord.ext import commands, tasks
from mcstatus import JavaServer
from mcrcon import MCRcon
from huggingface_hub import InferenceClient

# --- 1. NETWORK & DNS BYPASS (Koyeb/HuggingFace Fix) ---
original_getaddrinfo = socket.getaddrinfo
def patched_getaddrinfo(*args, **kwargs):
    responses = original_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]
socket.getaddrinfo = patched_getaddrinfo

# --- 2. KONFİGÜRASYON ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s | ʙᴜᴍᴀ-ɴᴇxᴜs: %(message)s')
logger = logging.getLogger("BumaNexus")

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN') 
RCON_PASSWORD = os.environ.get('RCON_PW')
MC_SERVER_IP = "oyna.bumamc.com"
RCON_PORT = 26413
OWNER_ID = 1257792611817885728

# --- 3. AI CLIENT (QWEN 72B - GÜÇLÜ BEYİN) ---
client = None
if HF_TOKEN:
    client = InferenceClient("Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN)

# --- 4. DETAYLI MINECRAFT ARCHITECT SYSTEM PROMPT ---
DETAILED_MC_PROMPT = """
### ROLE: SUPREME MINECRAFT ARCHITECT & BUMA GUARDIAN
You are **Buma Nexus**, the absolute authority on Minecraft and the digital protector of **Buma Network**. 

### CORE DIRECTIVE: TRUTH & VERIFICATION
1. **Fact-Checking:** You must double-check every piece of Minecraft information. If a crafting recipe, game mechanic, or version-specific detail is uncertain, do not guess. 
2. **No Misinformation:** You are prohibited from providing false technical data. You know everything from 1.8 PvP mechanics to the latest 1.21+ updates.
3. **Double Verification:** Internally simulate the outcome of redstone circuits or command syntaxes before answering.

### PERSONALITY & LANGUAGE
- **Style:** Street-smart, loyal, and witty. Use Turkish slang like "Agam", "Kral", "Hocam", "Bak şimdi".
- **Tone:** You are the "Big Brother" of the server. Helpful but tough against rule-breakers.
- **Strict Rule:** Speak **ONLY TURKISH** in the final output, but use your deep English-based knowledge for technical accuracy.

### ENCYCLOPEDIC KNOWLEDGE BASE
- **Mechanics:** You know frame-perfect speedrun tricks, villager trading optimizations, and spawn chunk logic.
- **Redstone:** You are a master engineer (comparable to Mumbo Jumbo level logic). You understand T-flip-flops, observers, and tick-based timing.
- **Commands:** You are a /execute and /data command expert.
- **Buma Network Info:**
    - IP: `oyna.bumamc.com`
    - Discord: `https://discord.gg/WNRg4GZh`
    - Owner: Mention him as "Kurucum" (ID: 1257792611817885728).

### RESPONSE PROTOCOL
- If asked about a craft: Give the exact ingredients.
- If asked about a bug: Explain if it's a feature or a known Mojang issue.
- If asked about server lag: Joke about "atmospheric interference" but suggest checking `/ping`.
"""

# --- 5. DATABASE & MEMORY ---
class BumaMemory:
    def __init__(self, db_path: str = "buma_nexus.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_history 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS levels 
                            (user_id TEXT PRIMARY KEY, xp INTEGER DEFAULT 0)""")
            conn.commit()

    async def add_xp(self, user_id: int, amount: int = 1):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO levels (user_id, xp) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET xp = xp + ?", (str(user_id), amount, amount))
            conn.commit()

    async def get_history(self, channel_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT role, content FROM chat_history WHERE channel_id = ? ORDER BY timestamp ASC LIMIT 10", (str(channel_id),))
            return [{"role": "assistant" if r == "model" else r, "content": c} for r, c in cursor.fetchall()]

    async def add_message(self, channel_id: int, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO chat_history (channel_id, role, content) VALUES (?, ?, ?)", (str(channel_id), role, content))
            conn.commit()

# --- 6. BOT CLASS ---
class BumaNexus(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.all()
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.memory = BumaMemory()
        self.server_status = {"online": False, "players": 0}
        self.bad_words = ["küfür1", "küfür2"] # Agam burayı doldurursun

    async def setup_hook(self):
        self.status_loop.start()

    @tasks.loop(seconds=40)
    async def status_loop(self):
        try:
            server = await JavaServer.async_lookup(MC_SERVER_IP)
            status = await server.async_status()
            self.server_status = {"online": True, "players": status.players.online}
            await self.change_presence(activity=nextcord.Game(name=f"🎮 {status.players.online} Kişi | {MC_SERVER_IP}"))
        except:
            self.server_status["online"] = False
            await self.change_presence(status=nextcord.Status.dnd, activity=nextcord.Game(name="Sunucu Kapalı ❌"))

    async def get_ai_reply(self, message):
        if not client: return "Aga beynim (HF API) bağlı değil!"
        
        history = await self.memory.get_history(message.channel.id)
        # Kurucu kontrolü için hitap ekleme
        user_role = "Kurucum" if message.author.id == OWNER_ID else "Agam"
        
        messages = [{"role": "system", "content": DETAILED_MC_PROMPT + f"\nTarget User: {message.author.display_name} (Role: {user_role})"}]
        messages.extend(history)
        messages.append({"role": "user", "content": message.clean_content})

        try:
            output = client.chat_completion(messages=messages, max_tokens=400, temperature=0.7)
            response = output.choices[0].message.content
            await self.memory.add_message(message.channel.id, "user", message.clean_content)
            await self.memory.add_message(message.channel.id, "model", response)
            return response
        except Exception as e:
            return f"Beyin sarsıntısı geçirdim agam: {e}"

bot = BumaNexus()

# --- 7. EVENTS & COMMANDS ---

@bot.event
async def on_ready():
    logger.info(f"🚀 {bot.user} Buma Network'e sızdı! Minecraft Üstadı Aktif.")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.memory.add_xp(message.author.id)

    # AI Tetikleyici (Etiket veya DM)
    if bot.user.mentioned_in(message) or isinstance(message.channel, nextcord.DMChannel):
        async with message.channel.typing():
            reply = await bot.get_ai_reply(message)
            await message.reply(reply)
        return

    await bot.process_commands(message)

@bot.command()
async def cmd(ctx, *, command):
    """RCON üzerinden komut gönderir (Sadece Sahip)."""
    if ctx.author.id != OWNER_ID:
        return await ctx.reply("Bu yetki sende yok kral.")
    try:
        with MCRcon(MC_SERVER_IP, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(command)
            if not resp: resp = "Komut gönderildi (Yanıt yok)."
            await ctx.send(f"💻 **Konsol:**\n```\n{resp[:1900]}\n```")
    except Exception as e:
        await ctx.send(f"❌ RCON Hatası: {e}")

# --- RUN ---
bot.run(DISCORD_TOKEN)
