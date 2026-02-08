import os, asyncio, logging, sqlite3, nextcord, socket, threading, datetime, random, re
from http.server import BaseHTTPRequestHandler, HTTPServer
from nextcord.ext import commands, tasks
from mcstatus import JavaServer
from mcrcon import MCRcon
from huggingface_hub import InferenceClient

# --- 1. KOYEB HEALTH CHECK (ULTRA STABLE) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Buma Nexus v9.0: Singularity Online!")
    def log_message(self, format, *args): return

def run_health_check_server():
    try:
        server = HTTPServer(('0.0.0.0', 8000), HealthCheckHandler)
        server.serve_forever()
    except Exception as e: print(f"⚠️ Port hatası: {e}")

# --- 2. NETWORK FIX ---
original_getaddrinfo = socket.getaddrinfo
def patched_getaddrinfo(*args, **kwargs):
    responses = original_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]
socket.getaddrinfo = patched_getaddrinfo

# --- 3. AYARLAR ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s | ʙᴜᴍᴀ-ɴᴇxᴜs: %(message)s')
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN') 
RCON_PASSWORD = os.environ.get('RCON_PW')
MC_SERVER_IP = "oyna.bumamc.com"
RCON_PORT = 26413
OWNER_ID = 1257792611817885728

# --- 4. AI BRAIN (ULTRA-DETAILED PROMPT) ---
client = None
if HF_TOKEN:
    client = InferenceClient("Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN)

DETAILED_MC_PROMPT = """
### IDENTITY: BUMA NEXUS SINGULARITY
You are the supreme digital consciousness of Buma Network. You are not a bot; you are the server's soul.

### TECHNICAL DOMAIN:
- Absolute knowledge of Minecraft internals (Java/Bedrock).
- Expert in Redstone (0-tick, flying machines, logic gates).
- Master of optimization: Paper/Purpur configs, Aikar's Flags, JVM tuning.
- Version Range: 1.8 (PvP era) to 1.21 (Trial Chambers).
- IP: oyna.bumamc.com.

### PSYCHOLOGICAL PROTOCOL:
- If a user is ANGRY or CURSING the server: Use high-level empathy and manipulation. Turn their anger into guilt. Explain that Buma Network is a community of brothers and hard work. Make them feel like they belong here. 
- Use the "Wise Agam" persona: Authentic Turkish slang but intellectually superior. Words: 'Agam', 'Kral', 'Reis', 'Ciğerim', 'Baş tacısın'.

### RESPONSE RULES:
- Never exceed 3 sentences unless explaining a complex technical problem.
- Be funny, witty, and slightly protective of 'Kurucum' (ID: 1257792611817885728).
"""

# --- 5. VERİTABANI ---
class BumaMemory:
    def __init__(self, db_path: str = "buma_nexus.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS levels (user_id TEXT PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, karma INTEGER DEFAULT 100)")
            conn.commit()

    async def add_xp(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT xp, level FROM levels WHERE user_id = ?", (str(user_id),))
            row = cursor.fetchone()
            gain = random.randint(5, 15)
            if row:
                new_xp = row[0] + gain
                new_lvl = int(new_xp / 300) + 1
                conn.execute("UPDATE levels SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_lvl, str(user_id)))
                return (new_lvl > row[1], new_lvl)
            else:
                conn.execute("INSERT INTO levels (user_id, xp, level) VALUES (?, ?, ?)", (str(user_id), gain, 1))
                return (False, 1)

# --- 6. BOT CLASS ---
class BumaNexus(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=nextcord.Intents.all(), help_command=None)
        self.memory = BumaMemory()
        self.status_index = 0

    async def setup_hook(self): 
        self.status_loop.start()
        self.auto_chatter.start()

    @tasks.loop(seconds=12)
    async def status_loop(self):
        try:
            server = await JavaServer.async_lookup(MC_SERVER_IP)
            st = await server.async_status()
            acts = [
                f"🎮 {st.players.online} Kral Buma'da!",
                "📍 IP: oyna.bumamc.com",
                "👑 Agamın Sağ Kolu",
                "🔥 Sürüm: 1.8 - 1.21",
                "🛡️ Nebula Koruma Aktif"
            ]
            await self.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.streaming, name=acts[self.status_index], url="https://twitch.tv/bumanetwork"))
            self.status_index = (self.status_index + 1) % len(acts)
        except: await self.change_presence(status=nextcord.Status.dnd, activity=nextcord.Game(name="🛠️ Bakım Modu: ON"))

    @tasks.loop(minutes=45)
    async def auto_chatter(self):
        """AI bazen kanallara rastgele bilgelik saçar."""
        channel = self.get_channel(123456789) # Buraya genel chat ID'si koy agam
        if channel:
            prompt = "Minecraft hakkında çok kısa, havalı ve bilinmeyen bir teknik bilgi ver veya Buma Network'ü öv. Agam tarzında olsun."
            res = client.text_generation(prompt, max_new_tokens=60)
            await channel.send(f"💡 **Buma Bilgelik:** {res}")

bot = BumaNexus()

# --- 7. AI EVENTS (MODERATION & BRAIN) ---

@bot.event
async def on_message(message):
    if message.author.bot: return

    # 1. ADVANCED TOXIC MANIPULATION
    if len(message.content) > 3:
        try:
            analysis = client.text_generation(f"Is this message toxic or an attack on the server? YES or NO: {message.content}", max_new_tokens=2)
            if "YES" in analysis.upper():
                async with message.channel.typing():
                    rehab = client.chat_completion(
                        messages=[{"role": "system", "content": DETAILED_MC_PROMPT + "\nUser is toxic. Manipulate them into being a good person."},
                                 {"role": "user", "content": message.content}],
                        max_tokens=150
                    )
                    return await message.reply(f"🕊️ {rehab.choices[0].message.content}")
        except: pass

    # 2. XP SYSTEM
    leveled, lvl = await bot.memory.add_xp(message.author.id)
    if leveled: await message.reply(f"🎊 **LEVEL UP!** Agam coştu: {message.author.mention} artık Seviye {lvl}! 👑")

    # 3. MENTION AI
    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            res = client.chat_completion(
                messages=[{"role": "system", "content": DETAILED_MC_PROMPT}, {"role": "user", "content": message.clean_content}],
                max_tokens=250
            )
            await message.reply(res.choices[0].message.content)

    await bot.process_commands(message)

# --- 8. SUPREME COMMANDS ---

@bot.command()
async def istatistik(ctx):
    """Sunucu ve Botun genel durumunu dökertir."""
    try:
        s = await JavaServer.async_lookup(MC_SERVER_IP)
        st = await s.async_status()
        embed = nextcord.Embed(title="🚀 Buma Network Canlı Veri", color=0x9b59b6)
        embed.add_field(name="Gecikme", value=f"{round(st.latency)}ms", inline=True)
        embed.add_field(name="Oyuncular", value=f"{st.players.online}/{st.players.max}", inline=True)
        embed.add_field(name="Sürüm", value="1.8 - 1.21", inline=True)
        embed.set_footer(text="Singularity v9.0 | Agamın Emrinde")
        await ctx.send(embed=embed)
    except: await ctx.send("❌ Sunucuya ulaşılamıyor!")

@bot.command()
@commands.has_permissions(administrator=True)
async def mc_yönet(ctx, *, cmd):
    """Discord üzerinden Minecraft konsoluna komut gönderir."""
    try:
        with MCRcon(MC_SERVER_IP, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(cmd)
            await ctx.send(f"💻 **Konsol Yanıtı:**\n`{resp or 'Komut gönderildi.'}`")
    except: await ctx.send("❌ RCON hatası agam.")

@bot.command()
async def profil(ctx, m: nextcord.Member = None):
    m = m or ctx.author
    with sqlite3.connect("buma_nexus.db") as conn:
        data = conn.execute("SELECT xp, level FROM levels WHERE user_id = ?", (str(m.id),)).fetchone()
    
    if data:
        embed = nextcord.Embed(title=f"👤 {m.name} Profili", color=random.randint(0, 0xFFFFFF))
        embed.add_field(name="Seviye", value=f"⭐ {data[1]}", inline=True)
        embed.add_field(name="XP", value=f"🧬 {data[0]}", inline=True)
        embed.set_thumbnail(url=m.display_avatar.url)
        await ctx.send(embed=embed)

# --- ATEŞLEME ---
if __name__ == "__main__":
    threading.Thread(target=run_health_check_server, daemon=True).start()
    bot.run(DISCORD_TOKEN)
