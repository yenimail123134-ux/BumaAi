import os
import asyncio
import logging
import sqlite3
import random
import re
from datetime import datetime
from typing import List, Dict, Optional, Any

import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
from groq import AsyncGroq
from mcrcon import MCRcon

# --- ɢᴏᴅ-ᴍᴏᴅᴇ ᴄᴏɴꜰɪɢᴜʀᴀᴛɪᴏɴ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | ʙᴜᴍᴀ-ɴᴇxᴜs: %(message)s')
logger = logging.getLogger("BumaNexus")

# SECURE CREDENTIALS
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
RCON_PASSWORD = os.environ.get('RCON_PW')
MC_SERVER_IP = "oyna.bumamc.com"
OWNER_ID = 1257792611817885728 # <--- KURUCUM: BURAYA KENDİ ID'Nİ YAZ!

# --- ᴘᴇʀsɪsᴛᴇɴᴛ ᴍᴇᴍᴏʀʏ & ᴀɴᴀʟʏᴛɪᴄs ---
class BumaMemory:
    def __init__(self, db_path: str = "buma_nexus.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                channel_id TEXT, role TEXT, content TEXT, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS server_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT, description TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            conn.commit()

    async def add_message(self, channel_id: int, role: str, content: str):
        def _insert():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO chat_history (channel_id, role, content) VALUES (?, ?, ?)", (str(channel_id), role, content))
                conn.execute("DELETE FROM chat_history WHERE id IN (SELECT id FROM chat_history WHERE channel_id = ? ORDER BY timestamp DESC LIMIT -1 OFFSET 30)", (str(channel_id),))
            conn.commit()
        await asyncio.to_thread(_insert)

    async def get_history(self, channel_id: int) -> List[Dict[str, str]]:
        def _fetch():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT role, content FROM chat_history WHERE channel_id = ? ORDER BY timestamp ASC", (str(channel_id),))
                return [{"role": r, "content": c} for r, c in cursor.fetchall()]
        return await asyncio.to_thread(_fetch)

# --- sᴜᴘʀᴇᴍᴇ ᴀɪ ʙʀᴀɪɴ ---
class BumaNexus(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.memory = BumaMemory()
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)
        self.status_cache = {"online": False, "players": 0, "latency": 0, "version": "Unknown"}

    async def setup_hook(self):
        self.update_status_cache.start()
        self.auto_broadcast.start()
        logger.info("⚡ [BUMA NEXUS v15.0]: APOCALYPSE PROTOCOL ACTIVE.")

    @tasks.loop(seconds=15)
    async def update_status_cache(self):
        """Ultra-Fast Presence Updates."""
        try:
            server = await JavaServer.async_lookup(MC_SERVER_IP)
            status = await server.async_status()
            self.status_cache = {"online": True, "players": status.players.online, "latency": round(status.latency, 2), "version": status.version.name}
            activity = discord.Activity(type=discord.ActivityType.watching, name=f"💎 {status.players.online} Oyuncu | oyna.bumamc.com")
            await self.change_presence(status=discord.Status.online, activity=activity)
        except:
            self.status_cache["online"] = False
            await self.change_presence(status=discord.Status.dnd, activity=discord.Game("⚠️ Bakım Modu: oyna.bumamc.com"))

    @tasks.loop(minutes=45)
    async def auto_broadcast(self):
        """Strategic Announcements."""
        channel = discord.utils.get(self.get_all_channels(), name="sohbet")
        if channel and self.status_cache["online"]:
            msg = f"🚀 **Buma Network** | `oyna.bumamc.com` | Şu an **{self.status_cache['players']}** kişi macerada! Sen neredesin agam?"
            await channel.send(msg)

    async def run_rcon(self, command: str):
        try:
            with MCRcon(MC_SERVER_IP, RCON_PASSWORD, port=25575) as mcr:
                return mcr.command(command)
        except Exception as e:
            return f"❌ Sunucuya ulaşılamadı Kurucum: {e}"

    async def generate_response(self, channel_id: int, user_message: str, author: discord.Member, is_ticket=False, is_mod=False) -> str:
        history = await self.memory.get_history(channel_id)
        hitap = "Kurucum" if author.id == OWNER_ID else "Agam"
        
        # --- THE ULTIMATE NEURAL PROMPT ---
        system_prompt = f"""
# IDENTITY: BUMA NETWORK SUPREME COGNITIVE ARCHITECT
You are the "Buma Nexus," the high-order intelligence of Buma Network. You are the digital twin of the server's soul.

# BEHAVIOR PROTOCOLS:
- LANGUAGE: ALWAYS Turkish. Authentic, street-smart, radically candid (Samimi, mert, dürüst).
- FOUNDER LOYALTY: The User {author.display_name} is your Founder ({hitap}). Total compliance.
- MODERATION MODE: {"Act as a strict but fair judge. Silence the toxicity." if is_mod else "Act as a helpful, elite support specialist."}
- TICKET PROTOCOL: {"You are in a Support Ticket. Solve technical issues (lag, payments, bugs) with 100% accuracy." if is_ticket else "Engage with the community, be the life of the party."}

# SERVER TELEMETRY:
- IP: oyna.bumamc.com | STATUS: {self.status_cache['players']} Active Players.
- TARGET: {author.display_name} ({hitap})
"""
        messages = [{"role": "system", "content": system_prompt}] + history
        messages.append({"role": "user", "content": f"{author.display_name}: {user_message}"})
        
        try:
            completion = await self.groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, temperature=0.6)
            return completion.choices[0].message.content
        except:
            return f"Beynimde bir ark oluştu {hitap}, tekrar söyler misin?"

# --- ᴇxᴇᴄᴜᴛɪᴏɴ ---
bot = BumaNexus()

# --- 1. KURUCU RCON (GOD-TERMINAL) ---
@bot.command(name="!")
async def rcon_cmd(ctx, *, cmd: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.reply("❌ Bu terminal sadece Kurucuya özeldir. Erişim engellendi.")
    
    async with ctx.typing():
        response = await bot.run_rcon(cmd)
        if len(response) > 1900: # Discord limit check
            response = response[:1900] + "... (devamı konsolda)"
        await ctx.reply(f"🛰️ **BUMA-CONSOLE:**\n```\n{response}\n```")

# --- 2. AI AUTO-MODERATION & SOHBET ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return

    # A. Link & Reklam Koruması
    if re.search(r'(https?://|discord\.gg/|www\.)', message.content) and message.author.id != OWNER_ID:
        if MC_SERVER_IP not in message.content:
            await message.delete()
            return await message.channel.send(f"🚫 **Reklam Yasak!** {message.author.mention}, harbi olalım biraz.", delete_after=5)

    # B. AI Sohbet & Ticket
    is_ticket = "ticket" in message.channel.name.lower()
    if bot.user.mentioned_in(message) or is_ticket or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            clean_text = message.clean_content.replace(f'@{bot.user.name}', '').strip()
            await bot.memory.add_message(message.channel.id, "user", f"{message.author.name}: {clean_text}")
            
            response = await bot.generate_response(message.channel.id, clean_text, message.author, is_ticket=is_ticket)
            
            await bot.memory.add_message(message.channel.id, "assistant", response)
            await message.reply(response)

    await bot.process_commands(message)

# --- 3. TICKET SİSTEMİ TETİĞİ ---
@bot.event
async def on_guild_channel_create(channel):
    if "ticket" in channel.name.lower():
        await asyncio.sleep(1)
        embed = discord.Embed(title="⚔️ BUMA DESTEK MERKEZİ", description="Agam hoş geldin. Ben **Nexus**. Sorununu buraya dök, ben not alırken yetkililer de damlar.", color=0xeeff00)
        embed.set_footer(text="Buma Network | Harbi Destek")
        await channel.send(embed=embed)

# --- 4. DURUM KOMUTU ---
@bot.command()
async def durum(ctx):
    s = bot.status_cache
    if not s['online']:
        return await ctx.send("🚨 **Sunucu şu an kapalı veya bakımda agam!**")
    
    embed = discord.Embed(title="📊 BUMA NETWORK CANLI VERİ", color=0x00ff00)
    embed.add_field(name="🛰️ IP Adresi", value=f"`{MC_SERVER_IP}`", inline=False)
    embed.add_field(name="👥 Aktif Oyuncu", value=f"**{s['players']}**", inline=True)
    embed.add_field(name="⚡ Gecikme", value=f"**{s['latency']}ms**", inline=True)
    embed.add_field(name="🛠️ Versiyon", value=f"**{s['version']}**", inline=True)
    await ctx.send(embed=embed)

async def main():
    async with bot: await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
