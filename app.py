import discord
import os
from groq import Groq 
import http.server
import threading

# --- 1. RENDER PORT VE SUNUCU ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Buma AI (Groq Edition) is RUNNING!")
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, TinyHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- 2. AYARLAR --- [cite: 2026-02-02, 2026-02-03]
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GROQ_API_KEY = "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" # Aldığın keyi buraya koy agam

client_groq = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True 
client_discord = discord.Client(intents=intents)

@client_discord.event
async def on_ready():
    print(f'Buma AI Groq Motoruyla AKTİF! IP: oyna.bumamc.com [cite: 2026-02-03]')

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user: return
    
    # Etiketlenince veya DM gelince çalış
    if client_discord.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            try:
                user_text = message.clean_content.replace(f'@{client_discord.user.name}', '').strip()
                
                # GROQ (Llama 3.3) SORGUSU
                completion = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile", # Şu anki en dahi ve hızlı model
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Sen Buma Network (oyna.bumamc.com) Minecraft sunucusunun dahi asistanısın. "
                                "Oyunculara her zaman 'agam' diye hitap et. Samimi, fırlama ve dahi ol. "
                                "IP Adresimiz: oyna.bumamc.com [cite: 2026-02-03]"
                            )
                        },
                        {"role": "user", "content": user_text}
                    ]
                )
                
                response = completion.choices[0].message.content
                await message.reply(response[:2000])

            except Exception as e:
                print(f"HATA: {e}")
                await message.reply(f"Groq beynimde kısa devre oldu agam! (Detay: {str(e)[:30]}...)")

client_discord.run(DISCORD_TOKEN)
