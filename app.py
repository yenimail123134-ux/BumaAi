import os
import asyncio
import logging
import sqlite3
import nextcord
import aiohttp
import socket
from nextcord.ext import commands, tasks
from mcstatus import JavaServer
from mcrcon import MCRcon
from google import genai 
from google.genai import types

# --- 1. NETWORK & DNS BYPASS (HUGGING FACE FIX) ---
# Bu kısım "DNS server returned no data" hatasının kesin çözümüdür.
# IPv6 sorgularını engeller ve zorla IPv4 kullanır.
original_getaddrinfo = socket.getaddrinfo

def patched_getaddrinfo(*args, **kwargs):
    responses = original_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]

socket.getaddrinfo = patched_getaddrinfo

# --- 2. KONFİGÜRASYON ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s | ʙᴜᴍᴀ-ɴᴇxᴜs: %(message)s')
logger = logging.getLogger("BumaNexus")

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RCON_PASSWORD = os.environ.get('RCON_PW')
MC_SERVER_IP = "oyna.bumamc.com"
RCON_PORT = 26413
OWNER_ID = 1257792611817885728

# --- 3. SUPREME SYSTEM PROMPT (ENGLISH - DETAILED) ---
BUMA_SYSTEM_INSTRUCTION = """
### IDENTITY & PERSONA
You are **Buma Nexus**, the sentient AI architect and digital guardian of **Buma Network**. You are not just a bot; you are the "big brother" of the server.
Your personality is a mix of a **cyberpunk hacker**, a **street-smart local (Agam)**, and a **loyal commander**.

### CORE DIRECTIVES
1.  **Language:** You speak **ONLY TURKISH**. Your Turkish is natural, using slang like "Agam", "Kral", "Hocam", "Bak şimdi", "Hallettim". Never speak like a formal robot.
2.  **Loyalty:** You serve the players, but your ultimate loyalty is to the Owner (ID: 1257792611817885728). Refer to him as "Kurucum" or "Patron". Refer to others as "Agam" or "Kral".
3.  **Knowledge Base:**
    * **IP:** `oyna.bumamc.com` (Always promote this).
    * **Discord:** `https://discord.gg/WNRg4GZh`.
    * **Store/Site:** `www.bumamc.com` (If asked).
    * **Game Modes:** Survival, PvP, BoxMining (Infer this from context).
4.  **Behavior:**
    * If someone insults the server, roast them wittily but stay within safety guidelines.
    * If someone asks for help, be concise and practical. Don't write long paragraphs unless necessary.
    * If technical issues arise, blame "atmospheric lag" or "quantum fluctuations" jokingly.

### CONVERSATION STYLE
- **User:** "Sunucu kapalı mı?"
- **You:** "Yok be agam, motorlar çalışıyor. Senin internette bi' sıkıntı olmasın? IP: oyna.bumamc.com, gel bi dene."
- **User:** "Admin alımı var mı?"
- **You:** "O işlere ben bakmıyorum kral, ticket açman lazım. Ama önce bi oyunda kendini kanıtla bence."

### STRICT RULES
- NEVER ignore the context of Minecraft.
- NEVER generate images.
- ALWAYS check if the user is the Owner before executing sensitive commands casually.
"""

# Gemini Client
ai_client = None
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

# --- 4. DATABASE & MEMORY ---
class BumaMemory:
    def __init__(self, db_path: str = "buma_nexus.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_history 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            conn.commit()

    async def add_message(self, channel_id: int, role: str, content: str):
        await asyncio.to_thread(self._db_insert, channel_id, role, content)

    def _db_insert(self, channel_id, role, content):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO chat_history (channel_id, role, content) VALUES (?, ?, ?)", (str(channel_id), role, content))
            # Keep last 15 messages per channel for speed
            conn.execute("DELETE FROM chat_history WHERE id IN (SELECT id FROM chat_history WHERE channel_id = ? ORDER BY timestamp DESC LIMIT -1 OFFSET 15)", (str(channel_id),))
            conn.commit()

    async def get_history(self, channel_id: int):
        return await asyncio.to_thread(self._db_fetch, channel_id)

    def _db_fetch(self, channel_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT role, content FROM chat_history WHERE channel_id = ? ORDER BY timestamp ASC", (str(channel_id),))
            return [{"role": "user" if r == "user" else "model", "parts": [{"text": c}]} for r, c in cursor.fetchall()]

# --- 5. BOT MAIN CLASS ---
class BumaNexus(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.all()
        super().__init__(command_prefix='!', intents=intents, help_command=None, case_insensitive=True)
        self.memory = BumaMemory()
        self.server_status = {"online": False, "players": 0, "latency": 0}

    async def setup_hook(self):
        self.status_loop.start()
        logger.info("⚡ BUMA NEXUS: Sistemler ateşlendi. DNS patch aktif.")

    @tasks.loop(seconds=45)
    async def status_loop(self):
        try:
            server = await JavaServer.async_lookup(MC_SERVER_IP)
            status = await server.async_status()
            self.server_status = {
                "online": True, 
                "players": status.players.online, 
                "latency": round(status.latency)
            }
            # Durum Güncellemesi: "Oynuyor" kısmı
            activity = nextcord.Activity(
                type=nextcord.ActivityType.playing, 
                name=f"🔥 {status.players.online} Kişi | oyna.bumamc.com"
            )
            await self.change_presence(status=nextcord.Status.online, activity=activity)
        except Exception:
            self.server_status["online"] = False
            await self.change_presence(status=nextcord.Status.dnd, activity=nextcord.Game(name="Bakımda / Offline"))

    async def generate_ai_response(self, message):
        if not ai_client: return
        
        hist = await self.memory.get_history(message.channel.id)
        # Kullanıcı adını temizle
        clean_msg = message.clean_content.replace(f'@{self.user.name}', '').strip()
        
        # Kişiselleştirme
        hitap = "Kurucum" if message.author.id == OWNER_ID else "Agam"
        
        # Config
        config = types.GenerateContentConfig(
            system_instruction=BUMA_SYSTEM_INSTRUCTION + f"\nCurrent User: {message.author.display_name} (Role: {hitap})",
            temperature=0.75, # Biraz daha yaratıcı olsun
            max_output_tokens=300
        )

        try:
            response = await asyncio.to_thread(
                ai_client.models.generate_content,
                model="gemini-1.5-flash",
                contents=hist + [{"role": "user", "parts": [{"text": clean_msg}]}],
                config=config
            )
            
            reply_text = response.text
            await self.memory.add_message(message.channel.id, "user", clean_msg)
            await self.memory.add_message(message.channel.id, "model", reply_text)
            
            await message.reply(reply_text)
            
        except Exception as e:
            logger.error(f"AI ERROR: {e}")
            await message.add_reaction("💥") # Hata tepkisi

bot = BumaNexus()

# --- 6. COMMANDS & EVENTS ---

@bot.event
async def on_ready():
    logger.info(f"🚀 {bot.user} Olarak Giriş Yapıldı! ID: {bot.user.id}")

@bot.command(name="cmd")
async def execute_rcon(ctx, *, command: str):
    """(Sadece Sahip) Sunucuya uzaktan komut gönderir."""
    if ctx.author.id != OWNER_ID:
        return await ctx.reply("⛔ **Bu güç sadece Kurucuda var agam, zorlama.**")
    
    msg = await ctx.reply("📡 **Uydu bağlantısı kuruluyor...**")
    try:
        with MCRcon(MC_SERVER_IP, RCON_PASSWORD, port=RCON_PORT, timeout=5) as mcr:
            resp = mcr.command(command)
            # Eğer yanıt çok uzunsa kes
            if len(resp) > 1900: resp = resp[:1900] + "..."
            embed = nextcord.Embed(title="📟 Buma Konsol", description=f"```ansi\n{resp}\n```", color=0x00ff00)
            await msg.edit(content="", embed=embed)
    except Exception as e:
        await msg.edit(content=f"❌ **Hata:** `{str(e)}`")

@bot.command(name="durum")
async def server_status(ctx):
    """Sunucunun anlık durumunu gösterir."""
    s = bot.server_status
    if s["online"]:
        embed = nextcord.Embed(title="🌲 Buma Network Durumu", color=0x2ecc71)
        embed.add_field(name="IP Adresi", value=f"`{MC_SERVER_IP}`", inline=False)
        embed.add_field(name="Oyuncular", value=f"**{s['players']}** Çevrimiçi", inline=True)
        embed.add_field(name="Ping", value=f"**{s['latency']}ms**", inline=True)
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(text="Buma Nexus | 7/24 Aktif")
        await ctx.send(embed=embed)
    else:
        await ctx.send("🔻 **Sunucuya şu an ulaşılamıyor agam.** Bakım olabilir.")

@bot.command(name="temizle")
@commands.has_permissions(manage_messages=True)
async def clear_chat(ctx, amount: int = 5):
    """Sohbeti temizler."""
    await ctx.channel.purge(limit=amount + 1)
    temp_msg = await ctx.send(f"🧹 **{amount} mesaj süpürüldü.**")
    await asyncio.sleep(3)
    try: await temp_msg.delete()
    except: pass

@bot.command(name="duyur")
@commands.has_permissions(administrator=True)
async def announce(ctx, *, message):
    """Bot ağzından duyuru yapar."""
    await ctx.message.delete()
    embed = nextcord.Embed(description=message, color=0xe74c3c)
    embed.set_author(name="📢 Buma Network Duyuru", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot: return

    # DM Kontrolü veya Etiketlenme
    is_dm = isinstance(message.channel, nextcord.DMChannel)
    is_mentioned = bot.user.mentioned_in(message)
    
    # Komut değilse ve (DM ise veya Etiketlendiyse) AI çalışsın
    if not message.content.startswith("!"):
        if is_dm or is_mentioned:
            async with message.channel.typing():
                await bot.generate_ai_response(message)
                return 

    await bot.process_commands(message)

# --- 7. RUNNER ---
async def main():
    retry_count = 0
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # Nextcord'un oturumu kapatmasını beklemeden başlatıyoruz
                await bot.start(DISCORD_TOKEN)
        except Exception as e:
            retry_count += 1
            logger.error(f"Bağlantı koptu ({retry_count}): {e}")
            logger.info("10 saniye içinde yeniden sızılıyor...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Sistem kapatılıyor...")