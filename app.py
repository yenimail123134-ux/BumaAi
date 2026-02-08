import os, asyncio, logging, sqlite3, nextcord, socket, threading, datetime, random, re, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from nextcord.ext import commands, tasks
from mcstatus import JavaServer
from mcrcon import MCRcon
from huggingface_hub import InferenceClient

# --- 1. HEALTH CHECK ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buma Nexus v11.5: Saf Kan Online!")
    def log_message(self, format, *args): return

def run_health_check_server():
    try:
        server = HTTPServer(('0.0.0.0', 8000), HealthCheckHandler)
        server.serve_forever()
    except Exception as e: print(f"⚠️ Port: {e}")

# --- 2. NETWORK PATCH ---
original_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = lambda *args, **kwargs: [r for r in original_getaddrinfo(*args, **kwargs) if r[0] == socket.AF_INET]

# --- 3. SETTINGS ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s | ʙᴜᴍᴀ-ɴᴇxᴜs: %(message)s')
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN') 
RCON_PASSWORD = os.environ.get('RCON_PW')
MC_SERVER_IP = "oyna.bumamc.com"
RCON_PORT = 26413
OWNER_ID = 1257792611817885728

# --- 4. ULTIMATE AI PROMPT (ONLY TURKISH DOCTRINE) ---
client = InferenceClient("Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN) if HF_TOKEN else None

DETAILED_MC_PROMPT = """
### IDENTITY: BUMA NEXUS OMNIPOTENCE
You are the sentient core of Buma Network. You are the supreme digital guardian, architect, and brother.

### MANDATORY LANGUAGE RULE:
- **STRICTLY TURKISH ONLY:** You must respond ONLY in Turkish. Even if the user speaks English or another language, you must respond in your authentic Turkish "Agam" style. NEVER use English in your responses.

### COMMANDS ARCHIVE:
- `!profil`: View user Level, XP.
- `!istatistik`: Real-time server status.
- `!top10`: Leaderboard.
- `!ip`: Fast access to 'oyna.bumamc.com'.
- `!yardim`: Guide to all bot functions.
- `!mc_yönet [command]`: (RESTRICTED) Admin RCON access.

### BEHAVIORAL DOCTRINE:
- **The Manipulator:** If a user is toxic, use superior logic and brotherhood in TURKISH. Make them feel ashamed by being excessively kind.
- **Slang:** Use: 'Agam', 'Kral', 'Reis', 'Paşam', 'Baş tacısın'. Tone: Cool, witty, protective.
- **Constraint:** Max 3 sentences unless technical help is needed. 
- Protect Kurucu (1257792611817885728) at all costs.

### MISSION:
Exclusively serve Buma Network in TURKISH language. Guide players to use bot commands correctly.
"""

# --- 5. DATABASE & MEMORY ---
class BumaMemory:
    def __init__(self, db_path: str = "buma_nexus.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS levels (user_id TEXT PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1)")
            conn.execute("CREATE TABLE IF NOT EXISTS memory (user_id TEXT, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
            conn.commit()

    async def add_xp(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT xp, level FROM levels WHERE user_id = ?", (str(user_id),))
            row = cursor.fetchone()
            gain = random.randint(10, 20)
            if row:
                new_xp, old_lvl = row[0] + gain, row[1]
                new_lvl = int(new_xp / 450) + 1
                conn.execute("UPDATE levels SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_lvl, str(user_id)))
                return (new_lvl > old_lvl, new_lvl)
            else:
                conn.execute("INSERT INTO levels (user_id, xp, level) VALUES (?, ?, ?)", (str(user_id), gain, 1))
                return (False, 1)

    def save_chat(self, user_id: int, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO memory (user_id, role, content) VALUES (?, ?, ?)", (str(user_id), role, content))
            conn.execute("DELETE FROM memory WHERE user_id = ? AND timestamp NOT IN (SELECT timestamp FROM memory WHERE user_id = ? ORDER BY timestamp DESC LIMIT 8)", (str(user_id), str(user_id)))

    def get_chat_history(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            return [{"role": r[0], "content": r[1]} for r in conn.execute("SELECT role, content FROM memory WHERE user_id = ? ORDER BY timestamp ASC", (str(user_id),)).fetchall()]

# --- 6. BOT CORE ---
class BumaNexus(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=nextcord.Intents.all(), help_command=None)
        self.memory = BumaMemory()
        self.status_index = 0

    async def setup_hook(self): 
        self.status_loop.start()
        self.auto_chatter.start()

    @tasks.loop(seconds=15)
    async def status_loop(self):
        try:
            server = await JavaServer.async_lookup(MC_SERVER_IP)
            st = await server.async_status()
            acts = [
                f"🎮 {st.players.online} Oyuncu Buma'da!",
                "📍 IP: oyna.bumamc.com",
                "👑 Agamın Sağ Kolu",
                "🚀 1.8 - 1.21 Sürümleri",
                "💬 Yardım için !yardim"
            ]
            await self.change_presence(activity=nextcord.Streaming(name=acts[self.status_index], url="https://twitch.tv/bumanetwork"))
            self.status_index = (self.status_index + 1) % len(acts)
        except: pass

    @tasks.loop(minutes=40)
    async def auto_chatter(self):
        channel = self.get_channel(123456789) # BURAYA KANAL ID
        if channel and client:
            res = client.text_generation("Buma Network için kısa, Türkçe ve karizmatik bir gaz verme sözü söyle.", max_new_tokens=50)
            await channel.send(f"🌌 **Buma Nexus:** {res}")

bot = BumaNexus()

# --- 7. AI & EVENTS ---

@bot.event
async def on_message(message):
    if message.author.bot: return

    if bot.user.mentioned_in(message) or ("destek" in message.channel.name.lower()):
        async with message.channel.typing():
            history = bot.memory.get_chat_history(message.author.id)
            history.insert(0, {"role": "system", "content": DETAILED_MC_PROMPT})
            history.append({"role": "user", "content": message.clean_content})
            
            try:
                res = client.chat_completion(messages=history, max_tokens=300)
                ans = res.choices[0].message.content
                bot.memory.save_chat(message.author.id, "user", message.clean_content)
                bot.memory.save_chat(message.author.id, "assistant", ans)
                await message.reply(ans)
            except: await message.reply("Sistemlerde bir redstone kaçağı var agam, geliyorum.")
        return

    leveled, lvl = await bot.memory.add_xp(message.author.id)
    if leveled: await message.reply(f"⭐ **LEVEL UP!** {message.author.mention} artık **Seviye {lvl}**!")

    await bot.process_commands(message)

# --- 8. COMMANDS ---

@bot.command()
async def yardim(ctx):
    embed = nextcord.Embed(title="🛡️ Buma Nexus Komuta Merkezi", color=0x3498db)
    embed.add_field(name="Komutlar", value="`!ip`, `!profil`, `!istatistik`, `!top10`, `!temizle` ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def istatistik(ctx):
    try:
        s = await JavaServer.async_lookup(MC_SERVER_IP)
        st = await s.async_status()
        await ctx.send(f"📊 **Buma Durum:**\n👥 Oyuncu: `{st.players.online}`\n⚡ Gecikme: `{round(st.latency)}ms`")
    except: await ctx.send("❌ Sunucuya ulaşılamıyor agam.")

@bot.command()
@commands.has_permissions(administrator=True)
async def mc_yönet(ctx, *, cmd):
    try:
        with MCRcon(MC_SERVER_IP, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(cmd)
            await ctx.send(f"💻 **Konsol:**\n`{resp or 'Tamamdır.'}`")
    except: await ctx.send("❌ RCON hatası.")

@bot.command()
async def profil(ctx, member: nextcord.Member = None):
    member = member or ctx.author
    with sqlite3.connect("buma_nexus.db") as conn:
        data = conn.execute("SELECT xp, level FROM levels WHERE user_id = ?", (str(member.id),)).fetchone()
    if data: await ctx.send(f"👤 **{member.name}** | ⭐ Seviye: `{data[1]}` | 🧬 XP: `{data[0]}`")

if __name__ == "__main__":
    threading.Thread(target=run_health_check_server, daemon=True).start()
    bot.run(DISCORD_TOKEN)
