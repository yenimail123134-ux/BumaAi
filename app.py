import discord
import os
import google.generativeai as genai

# Anahtarları Render üzerinden çekiyoruz
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini (Yapay Zeka) Kurulumu
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Discord Bot Yetkileri
intents = discord.Intents.default()
intents.message_content = True # Bu ayar Discord Developer Portal'da AÇIK olmalı!
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    # Bot bağlandığında konsola bilgi basar [cite: 2026-02-02]
    print(f'Buma AI Hazır! Giriş Adı: {client.user}')
    print('Sunucu: oyna.bumamc.com')

@client.event
async def on_message(message):
    # Kendi mesajlarına cevap vermesin [cite: 2026-02-02]
    if message.author == client.user: return
    
    # Bot etiketlendiğinde veya DM atıldığında çalışır [cite: 2026-02-02]
    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            try:
                # Buma Network'e özel dahi asistan kişiliği [cite: 2026-02-02]
                prompt = f"Sen Buma Network Minecraft sunucusunun dahi ve samimi asistanısın. Oyuncunun sorusu: {message.content}"
                response = model.generate_content(prompt)
                
                # Mesajı gönder
                await message.reply(response.text)
            except Exception as e:
                print(f"Hata oluştu: {e}")
                await message.reply("Şu an beynim biraz karıştı agam, tekrar sorar mısın?")

# Botu başlat
client.run(DISCORD_TOKEN)
