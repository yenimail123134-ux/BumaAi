import discord
from discord.ext import commands
import os, threading, http.server
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

# --- 3. HAFIZA SİSTEMİ (UNUTMAMASI İÇİN) ---
# Her kanal için son 10 mesajı aklında tutar
hafıza = {} 

def hafıza_yonet(kanal_id, rol, icerik):
    if kanal_id not in hafıza:
        hafıza[kanal_id] = []
    hafıza[kanal_id].append({"role": rol, "content": icerik})
    # Hafızayı taze tut: Son 10 mesajdan fazlasını sil (limit aşılmasın)
    if len(hafıza[kanal_id]) > 10:
        hafıza[kanal_id].pop(0)

# --- 4. SUNUCU DURUMU ---
def get_mc_status():
    try:
        server = JavaServer.lookup("oyna.bumamc.com")
        status = server.status()
        return f"Sunucu Aktif: {status.players.online} oyuncu içeride. [cite: 2026-02-03]"
    except: return "Sunucuya şu an ulaşılamıyor agam. [cite: 2026-02-03]"

# --- 5. ANA ZEKA VE HAFIZA ENTEGRASYONU ---

@bot.event
async def on_ready():
    print(f'Buma Harbi Moderator Hazır! IP: oyna.bumamc.com')

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # AI Destekli Kelime Filtresi
    if not message.author.guild_permissions.manage_messages:
        test = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Sadece küfür veya reklam varsa 'YASAK' yaz, yoksa 'TEMİZ' yaz."},
                      {"role": "user", "content": message.content}]
        )
        if "YASAK" in test.choices[0].message.content.upper():
            await message.delete()
            return

    # Bot etiketlendiğinde veya DM atıldığında
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            user_text = message.clean_content.replace(f'@{bot.user.name}', '').strip()
            
            # Hafızaya ekle
            hafıza_yonet(message.channel.id, "user", f"{message.author.display_name}: {user_text}")

            system_prompt = (
                "Sen Buma Network moderatörüsün. İsmin Buma AI. [cite: 2026-02-02] "
                "KURALLAR: \n"
                "1. Söylediğin her şeyi doğruluğu için iki kez kontrol et. Sadece gerçekleri söyle. [cite: 2026-02-02]\n"
                "2. ASLA robotik olma. Samimi, kısa ve öz konuş. Uzun 'inek' yazılarından kaçın. [cite: 2026-02-02]\n"
                "3. SADECE TÜRKÇE KONUŞ. [cite: 2026-02-02]\n"
                "4. Salih'e (Buma1) 'Kurucum' de, diğerlerine 'Agam' diye hitap et. [cite: 2026-02-02]\n"
                "5. Asla görsel oluşturma. [cite: 2026-01-28]\n"
                f"Güncel Sunucu Durumu: {get_mc_status()} [cite: 2026-02-03]"
            )

            # Groq'a tüm hafızayı gönder
            gonderilecek_mesajlar = [{"role": "system", "content": system_prompt}] + hafıza[message.channel.id]

            cevap = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=gonderilecek_mesajlar,
                temperature=0.6
            )
            
            ai_cevap = cevap.choices[0].message.content
            # AI cevabını da hafızaya ekle ki bir sonraki mesajda ne dediğini bilsin
            hafıza_yonet(message.channel.id, "assistant", ai_cevap)
            
            await message.reply(ai_cevap)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
