import discord
import os
from google import genai
import http.server
import threading

# --- RENDER PORT HATASI ÇÖZÜMÜ ---
# Render'ın "No open ports detected" hatasını engellemek için ufak bir sunucu
def run_dummy_server():
    server_address = ('', int(os.environ.get("PORT", 8080)))
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
# --------------------------------

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GEMINI_KEY = "AIzaSyAHc3B8saelCuZH9_wShhj-kOr2luGdQ58"

# Yeni Gemini Kurulumu
client_gemini = genai.Client(api_key=GEMINI_KEY)

intents = discord.Intents.default()
intents.message_content = True
client_discord = discord.Client(intents=intents)

@client_discord.event
async def on_ready():
    print(f'Buma AI (oyna.bumamc.com) Aktif! {client_discord.user}')

@client_discord.event
async def on_message(message):
    if message.author == client_discord.user: return
    
    if client_discord.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            try:
                # Yeni kütüphane formatı
                response = client_gemini.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=f"Sen Buma Network Minecraft sunucusunun (oyna.bumamc.com) dahi asistanısın: {message.content}"
                )
                await message.reply(response.text)
            except Exception as e:
                print(f"Hata: {e}")
                await message.reply("Beynimde bir kısa devre oldu agam, tekrar sor!")

client_discord.run(DISCORD_TOKEN)
