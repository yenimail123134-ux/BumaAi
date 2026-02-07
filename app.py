import discord
import os
import io
import re
import threading
import http.server
from datetime import datetime
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
from mcstatus import JavaServer
from PIL import Image

# --- 1. SUNUCU AYAKTA TUTMA (Render için) ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Buma AI (Full Edition) is RUNNING!")
    try:
        httpd = http.server.HTTPServer(('', port), TinyHandler)
        httpd.serve_forever()
    except Exception as e:
        print(f"Server hatası: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. AYARLAR VE TOKENLAR ---
# Render Environment Variables kısmından çekiyoruz agam
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN') 
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Eğer Render'a girmeden denemek istersen buraya tırnak içinde yazabilirsin:
if not GROQ_API_KEY:
    GROQ_API_KEY = "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"

client_groq = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Sunucu kişi sayısını çekmek için
client_discord = discord.Client(intents=intents)

# --- 3. YARDIMCI ARAÇLAR (MC ve YouTube) ---
def get_mc_status():
    try:
        server = JavaServer.lookup("oyna.bumamc.com")
        status = server.status()
        return f"Şu an sunucuda {status.players.online}/{status.players.max} oyuncu var. Sürüm: {status.version.name}"
    except:
        return "Sunucu şu an kapalı veya ulaşılamıyor agam."

def get_yt_transcript(url):
    video_id = None
    if "v=" in url: video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be" in url: video_id = url.split("/")[-1]
    if video_id:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr', 'en'])
            return " ".join([t['text'] for t in transcript])[:4000]
        except: return "Altyazı bulunamadı veya kapalı."
    return None

# --- 4. ANA BOT OLAYLARI ---
@client_discord.event
async def on_ready():
    print(f'--- Buma AI Aktif! Patron: Salih (Buma1) ---')

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user: return

    is_mentioned = client_discord.user.mentioned_in(message)
    is_dm = isinstance(message.channel, discord.DMChannel)

    if is_mentioned or is_dm:
        async with message.channel.typing():
            try:
                user_text = message.clean_content.replace(f'@{client_discord.user.name}', '').strip()
                
                # 1. Minecraft Verisi
                mc_info = get_mc_status()
                
                # 2. Görsel Analiz (Pillow Bilgisi)
                img_desc = ""
                if message.attachments:
                    for attach in message.attachments:
                        if any(attach.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                            img_data = await attach.read()
                            img = Image.open(io.BytesIO(img_data))
                            img_desc = f"\n[Görsel Bilgisi: {attach.filename}, Boyut: {img.size}]"

                # 3. YouTube Özeti
                yt_info = ""
                if "youtube.com" in user_text or "youtu.be" in user_text:
                    yt_text = get_yt_transcript(user_text)
                    if yt_text: yt_info = f"\nYouTube Video İçeriği: {yt_text}"

                # 4. Kurucu ve Ortam Tanıma
                role_info = "Oyuncu"
                uye_sayisi = message.guild.member_count if message.guild else "Bilinmiyor"
                if message.author.name == "salih070068":
                    role_info = "KURUCU/PATRON (Buma1)"

                # --- SİSTEM TALİMATI ---
                system_prompt = (
                    "Sen Buma Network (oyna.bumamc.com) Minecraft sunucusunun dahi asistanısın. "
                    f"Şu anki Sunucu Durumu: {mc_info}. "
                    f"Konuştuğun Kişi: {message.author.display_name} ({role_info}). "
                    f"Sunucu Üye Sayısı: {uye_sayisi}. "
                    "KURAL: Asla robotik olma. 'Agam' diye hitap et. Salih'e 'Patron' de. "
                    "Zeki, fırlama ve yardımsever ol. "
                    f"{img_desc}"
                    f"{yt_info}"
                )

                # GROQ SORGUSU (Llama 3.3)
                chat_completion = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0.8 # Daha insansı cevaplar
                )

                response = chat_completion.choices[0].message.content
                await message.reply(response[:2000])

            except Exception as e:
                print(f"Hata: {e}")
                await message.reply("Agam beynim yandı, bir terslik var! (Hata oluştu)")

# Botu Başlat
if DISCORD_TOKEN:
    client_discord.run(DISCORD_TOKEN)
else:
    print("HATA: DISCORD_TOKEN bulunamadı! Render panelinden Environment Variables ekle.")
