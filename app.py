import discord
import os
import io
from google import genai
import http.server
import threading

# --- RENDER PORT ÇÖZÜMÜ ---
def run_dummy_server():
    server_address = ('', int(os.environ.get("PORT", 8080)))
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- AYARLAR --- [cite: 2026-02-02]
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GEMINI_KEY = "AIzaSyDQxzO_DgAjDy0VwXWhw_ztpeUpARv85TQ" # Yeni anahtarın [cite: 2026-02-02]

client_gemini = genai.Client(api_key=GEMINI_KEY)
intents = discord.Intents.default()
intents.message_content = True
client_discord = discord.Client(intents=intents)

@client_discord.event
async def on_ready():
    print(f'Buma AI (oyna.bumamc.com) Aktif! [cite: 2026-02-03]')

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user: return
    
    # Botun etiketlenmesi veya DM durumu
    if client_discord.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            try:
                content_list = []
                
                # 1. GÖRSEL ANALİZİ (Dosya gönderildiyse) [cite: 2026-02-02]
                if message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                            img_data = await attachment.read()
                            content_list.append({"mime_type": "image/jpeg", "data": img_data})
                
                # 2. METİN ANALİZİ
                user_text = message.clean_content.replace(f'@{client_discord.user.name}', '').strip()
                prompt = (
                    "Sen Buma Network (oyna.bumamc.com) Minecraft sunucusunun dahi, samimi ve "
                    "zaman zaman esprili asistanısın. Oyunculara 'agam' diye hitap et. "
                    "Eğer mesajda küfür varsa samimiyetle uyar ama cevabını dahi bir dille ver. "
                    f"Kullanıcı: {user_text}"
                )
                content_list.append(prompt)

                # 3. GEMINI CEVAP (Güvenlik filtreleri esnetildi) [cite: 2026-02-02]
                response = client_gemini.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=content_list,
                    config={
                        "safety_settings": [
                            {"category": "HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARASSMENT", "threshold": "BLOCK_NONE"}
                        ]
                    }
                )
                
                if response.text:
                    await message.reply(response.text)
                else:
                    await message.reply("Gördüklerim/duyduklarım karşısında dilim tutuldu agam, tekrar sor!")

            except Exception as e:
                print(f"Hata: {e}")
                await message.reply("Şu an beynim biraz karıştı agam, tekrar sorar mısın?")
