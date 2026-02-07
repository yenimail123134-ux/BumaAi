import discord
import os
import io
from google import genai
import http.server
import threading

# --- 1. RENDER İÇİN KESİN PORT ÇÖZÜMÜ ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Buma AI is RUNNING!")
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()
            
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, TinyHandler)
    print(f"--- Buma Sunucusu {port} portunda dinliyor ---")
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. AYARLAR --- [cite: 2026-02-02, 2026-02-03]
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_KEY', "AIzaSyDQxzO_DgAjDy0VwXWhw_ztpeUpARv85TQ")
HEDEF_KANAL_ID = 1463174455130980433 

client_gemini = genai.Client(api_key=GEMINI_KEY)
intents = discord.Intents.default()
intents.message_content = True 
client_discord = discord.Client(intents=intents)

# --- 3. BOT OLAYLARI ---

@client_discord.event
async def on_ready():
    print(f'Buma AI (oyna.bumamc.com) AKTİF! [cite: 2026-02-03]')
    if HEDEF_KANAL_ID:
        try:
            channel = client_discord.get_channel(HEDEF_KANAL_ID)
            if channel:
                await channel.send("🚀 **Agam ben geldim!** Buma AI (oyna.bumamc.com) şu an aktif. Soruları alalım!")
        except Exception as e:
            print(f"Anons hatası: {e}")

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user: return
    
    if client_discord.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            try:
                content_parts = []
                
                # GÖRSEL İŞLEME: 400 hatasını önlemek için bytes formatı
                if message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                            img_data = await attachment.read()
                            # PIL (Image.open) kullanmadan direkt bytes ve mime_type gönderiyoruz
                            content_parts.append({
                                "mime_type": attachment.content_type or "image/jpeg",
                                "data": img_data
                            })
                
                # METİN İŞLEME [cite: 2026-02-02]
                user_text = message.clean_content.replace(f'@{client_discord.user.name}', '').strip()
                prompt = (
                    "Sen Buma Network (oyna.bumamc.com) dahi asistanısın. Oyunculara 'agam' de. "
                    "Görselleri Minecraft ve sunucu evreniyle bağdaştırarak yorumla. "
                    f"\n\nKullanıcı: {user_text if user_text else 'Görsel gönderdi.'}"
                )
                content_parts.append(prompt)

                # GEMINI CEVAP [cite: 2026-02-02]
                response = client_gemini.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=content_parts,
                    config={
                        "safety_settings": [
                            {"category": "HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARASSMENT", "threshold": "BLOCK_NONE"},
                            {"category": "DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                            {"category": "SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
                        ]
                    }
                )
                
                if response.text:
                    await message.reply(response.text[:2000])
                else:
                    await message.reply("Düşündüm ama bir şey diyemedim agam!")

            except Exception as e:
                print(f"HATA: {e}")
                # Hatanın ilk 40 karakterini kullanıcıya gösteriyoruz ki anlayalım
                await message.reply(f"Beynimde bir kısa devre oldu agam! (Detay: {str(e)[:40]}...)")

client_discord.run(DISCORD_TOKEN)
