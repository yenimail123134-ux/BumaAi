import discord
from discord.ext import commands
import os, io, threading, http.server
from groq import Groq
from mcstatus import JavaServer

# --- 1. RENDER CANLILIK DESTEĞİ ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Buma Harbi Moderator is ACTIVE!")
    httpd = http.server.HTTPServer(('', port), TinyHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. AYARLAR ---
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GROQ_API_KEY = "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"
client_groq = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- 3. SUNUCU DURUMU ---
def get_mc_status():
    try:
        server = JavaServer.lookup("oyna.bumamc.com")
        status = server.status()
        return f"Sunucu Aktif: {status.players.online} oyuncu içeride. [cite: 2026-02-03]"
    except: return "Sunucuya şu an ulaşılamıyor agam. [cite: 2026-02-03]"

# --- 4. SERT MODERASYON KOMUTLARI ---

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, miktar: int):
    """Mesajları temizler: !sil 10"""
    await ctx.channel.purge(limit=miktar + 1)
    await ctx.send(f"{miktar} mesajı süpürdüm patron. Tertemiz! ✨", delete_after=3)

@bot.command()
@commands.has_permissions(kick_members=True)
async def at(ctx, uye: discord.Member, *, sebep="Kural dışı hareket"):
    """Oyuncuyu sunucudan atar"""
    await uye.kick(reason=sebep)
    await ctx.send(f"{uye.display_name} kapının önüne konuldu. Sebep: {sebep}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def yasakla(ctx, uye: discord.Member, *, sebep="Ağır ihlal"):
    """Oyuncuyu banlar"""
    await uye.ban(reason=sebep)
    await ctx.send(f"{uye.display_name} biletini kestim, bir daha gelemez! 🔨")

# --- 5. ANA ZEKA VE FİLTRELEME ---

@bot.event
async def on_ready():
    print(f'Buma Harbi Moderator Hazır! IP: oyna.bumamc.com')

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # AI Destekli Kelime/Reklam Filtresi
    if not message.author.guild_permissions.manage_messages:
        test = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Sadece küfür veya reklam varsa 'YASAK' yaz, yoksa 'TEMİZ' yaz."},
                      {"role": "user", "content": message.content}]
        )
        if "YASAK" in test.choices[0].message.content.upper():
            await message.delete()
            return

    # Etiketleme veya DM durumunda dahi asistan devreye girer
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            user_text = message.clean_content.replace(f'@{bot.user.name}', '').strip()
            
            # SİSTEM TALİMATLARI (SENİN İSTEDİĞİN KURALLAR)
            system_prompt = (
                "Sen Buma Network moderatörüsün. İsmin Buma AI. [cite: 2026-02-02]"
                "KURALLAR: \n"
                "1. Söylediğin her şeyi doğruluğu için iki kez kontrol et. Sadece gerçekleri söyle. [cite: 2026-02-02]\n"
                "2. ASLA robotik olma. Samimi, kısa ve öz konuş. Uzun 'inek' yazılarından kaçın. [cite: 2026-02-02]\n"
                "3. SADECE TÜRKÇE KONUŞ. Araya İngilizce veya başka dil karıştırma. [cite: 2026-02-02]\n"
                "4. Salih'e (Buma1) 'Kurucum' de, diğerlerine 'Agam' diye hitap et. [cite: 2026-02-02]\n"
                "5. Asla görsel oluşturma. [cite: 2026-01-28]\n"
                f"Güncel Sunucu Durumu: {get_mc_status()} [cite: 2026-02-03]"
            )

            cevap = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}],
                temperature=0.6 # Daha tutarlı ve dürüst cevaplar için
            )
            await message.reply(cevap.choices[0].message.content)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
