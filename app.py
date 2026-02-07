import discord
import os
import io
from google import genai
from google.genai import types 
import http.server
import threading
import asyncio

# --- 1. RENDER İÇİN KESİN PORT ÇÖZÜMÜ ---
# Render genellikle 10000 portunu ister, bulamazsa 8080'i dener.
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    # Basit bir cevap döndüren handler
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Buma AI (oyna.bumamc.com) is RUNNING!")
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()
            
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, TinyHandler)
    print(f"--- Buma Sunucusu {port} portunda dinliyor ---")
    httpd.serve_forever()

# Sunucuyu arka planda başlat
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. AYARLAR VE ANAHTARLAR ---
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GEMINI_KEY = "AIzaSyDQxzO_DgAjDy0VwXWhw_ztpeUpARv85TQ" 

# Hangi kanala "Ben geldim" yazsın? (Kanal ID'sini buraya sayı olarak yaz)
# Örnek: HEDEF_KANAL_ID = 123456789012345678
HEDEF_KANAL_ID = 1335967657960308740 # <--- BURAYA KENDİ KANAL ID'Nİ YAPIŞTIR AGAM!

client_gemini = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True # Mesajları okuması için şart
client_discord = discord.Client(intents=intents)

# --- 3. BOT OLAYLARI ---

@client_discord.event
async def on_ready():
    print("--------------------------------------------------")
    print(f'Bot Giriş Yaptı: {client_discord.user}')
    print(f'Buma AI (oyna.bumamc.com) Tamamen Aktif!')
    print("--------------------------------------------------")
    
    # Bot açılınca Discord kanalına mesaj atma kısmı
    if HEDEF_KANAL_ID:
        try:
            channel = client_discord.get_channel(HEDEF_KANAL_ID)
            if channel:
                await channel.send("🚀 **Agam ben geldim!** Buma AI (oyna.bumamc.com) şu an aktif ve emrinize amade. Soruları alalım!")
        except Exception as e:
            print(f"Açılış mesajı atılamadı: {e}")

@client_discord.event
async def on_message(message):
    # Kendi mesajına cevap vermesin
    if message.author == client_discord.user: return
    
    # Sadece etiketlenince veya DM gelince çalışsın
    if client_discord.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            try:
                content_list = []
                
                # A. GÖRSEL KONTROLÜ
                if message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                            # Görseli belleğe indir
                            img_data = await attachment.read()
                            # Gemini'ye uygun formata çevir (Bytes -> PIL Image gerekmez, direkt bytes destekler ama format önemli)
                            # Google GenAI kütüphanesinde görseli 'types.Part' ile veya direkt bytes ile verebiliriz.
                            # En garantisi PIL image objesine çevirmektir ama kütüphane bytes da kabul eder.
                            from PIL import Image
                            image = Image.open(io.BytesIO(img_data))
                            content_list.append(image)
                
                # B. METİN KONTROLÜ
                user_text = message.clean_content.replace(f'@{client_discord.user.name}', '').strip()
                
                # Sistem Talimatı (System Instruction)
                prompt = (
                    "Sen Buma Network (oyna.bumamc.com) Minecraft sunucusunun dahi, samimi, esprili ve "
                    "biraz da fırlama asistanısın. Oyunculara her zaman 'agam' diye hitap et. "
                    "Sunucu IP'si: oyna.bumamc.com. "
                    "Eğer kullanıcı küfür ederse, samimi bir dille uyar ama asla tersleme. "
                    "Görsel atılırsa, görseli Minecraft evreniyle veya sunucuyla bağdaştırarak dahi yorumlar yap. "
                    f"\n\nKullanıcı Mesajı: {user_text}"
                )
                content_list.append(prompt)

                # C. GEMINI CEVAP (Güvenlik Ayarları MAX Seviyede Açık)
                response = client_gemini.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=content_list,
                    config={
                        "safety_settings": [
                            {"category": "HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARASSMENT", "threshold": "BLOCK_NONE"},
                            {"category": "SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                            {"category": "DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                        ]
                    }
                )
                
                # Cevabı gönder
                if response.text:
                    # Discord mesaj limiti 2000 karakterdir, gerekirse bölebiliriz ama şimdilik direkt atalım
                    await message.reply(response.text[:2000]) 
                else:
                    await message.reply("Agam, Google abimizden ses gelmedi, bir daha dener misin?")

            except Exception as e:
                # Hatayı konsola bas (Render Loglarında görmek için)
                print(f"HATA DETAYI: {e}")
                # Kullanıcıya hata mesajı (Hata detayını da ekledim ki sorunu anlayalım)
                await message.reply(f"Beynimde bir kısa devre oldu agam! (Teknik Hata: {str(e)[:50]}...)")

client_discord.run(DISCORD_TOKEN)
