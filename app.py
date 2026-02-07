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

# --- 1. SUNUCU AYAKTA TUTMA ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Buma AI (Full Edition) is RUNNING!")
    httpd = http.server.HTTPServer(('', port), TinyHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. AYARLAR ---
GROQ_API_KEY = "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"
client_groq = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client_discord = discord.Client(intents=intents)

# --- 3. YARDIMCI ARAÇLAR ---
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
            return " ".join([t['text'] for t in transcript])[:5000]
        except: return "Altyazı bulunamadı."
    return None

# --- 4. ANA OLAY ---
@client_discord.event
async def on_ready():
    print(f'Buma AI Aktif! Patron: Salih (Buma1)')

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user: return

    is_mentioned = client_discord.user.mentioned_in(message)
    is_dm = isinstance(message.channel, discord.DMChannel)

    if is_mentioned or is_dm:
        async with message.channel.typing():
            try:
                user_text = message.clean_content.replace(f'@{client_discord.user.name}', '').strip()
                mc_info = get_mc_status()
                
                # --- GÖRSEL ANALİZ (PILLOW) ---
                img_desc = ""
                if message.attachments:
                    for attach in message.attachments:
                        if any(attach.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                            img_data = await attach.read()
                            img = Image.open(io.BytesIO(img_data))
                            img_desc = f"[Görsel Algılandı: {attach.filename}, Boyut: {img.size}]"
                            # Groq Vision modelini burada kullanabilirsin ama şimdilik 'metin' odaklıyız.

                # --- YOUTUBE ANALİZ ---
                yt_info = ""
                if "youtube.com" in user_text or "youtu.be" in user_text:
                    yt_text = get_yt_transcript(user_text)
                    if yt_text: yt_info = f"\nYouTube Video İçeriği: {yt_text}"

                # --- KURUCU TANIMA ---
                role_info = "Oyuncu"
                if message.author.name == "salih070068":
                    role_info = "KURUCU/PATRON (Buma1)"

                # --- SİSTEM MESAJI (SALAKLIK GİDERİCİ) ---
                system_prompt = (
                    "Sen Buma Network (oyna.bumamc.com) Minecraft sunucusunun dahi asistanısın. "
                    f"Şu anki Sunucu Durumu: {mc_info}. "
                    f"Konuştuğun Kişi: {message.author.display_name} ({role_info}). "
                    "KURAL: Asla resmi olma. 'Agam' diye hitap et. Salih'e (Buma1) 'Patron' de. "
                    "Zeki, fırlama ve yardımsever ol. Bir toplulukta olduğunu bil. "
                    f"Gelen Görsel Bilgisi: {img_desc}"
                    f"{yt_info}"
                )

                # GROQ SORGUSU
                chat_completion = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0.7
                )

                await message.reply(chat_completion.choices[0].message.content)

            except Exception as e:
                print(f"Hata: {e}")
                await message.reply("Agam beynim yandı, bi' reset atsak mı? (Hata oluştu)")

client_discord.run(DISCORD_TOKEN)
