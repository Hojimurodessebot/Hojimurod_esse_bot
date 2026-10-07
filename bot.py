import os, asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

RUBRIC = """
Esse 12 kriteriy va jami 24 ball bo'yicha baholanadi:
1. Topshiriq talablarining bajarilganligi.
2. Ikki qarash va shaxsiy qarashning bayoni.
3. Har ikki qarashning dalillar bilan asoslanganligi.
4. Matn yaxlitligi: kirish, asosiy qism, xulosa.
5. Mantiqiy-qurilish va qismlar bog'liqligi.
6. Fikrlar tahlili va mantiqiy izchillik.
7. Imlo.
8. Punktuatsiya.
9. So'z qo'llash bilan bog'liq uslubiy xatolar.
10. So'z qo'llash va uslubiy yaxlitlik.
11. Lug'at boyligi va leksik xilma-xillik.
12. Keraksiz/sheva/vulgarizm/varvarizm/parazit birliklar.
Har bir kriteriy: 0, 0.5, 1, 1.5 yoki 2 ball. Jami 24 ball.
"""

async def analyze(essay):
    prompt = f"""Sen O'zbek tili va adabiyoti milliy sertifikat esse tekshiruvchisisan.
Esse-ni juda aniq va xolis tekshir. Har bir xatoni imkon qadar matndan iqtibos bilan ko'rsat.
{RUBRIC}

Natijani quyidagi tartibda ber:
1) 12 kriteriy jadvali: kriteriy, ball, asos, aniq topilmalar.
2) Imlo xatolari: soni va har biri.
3) Punktuatsiya xatolari: soni va har biri.
4) Uslubiy va lug'aviy xatolar.
5) Jami: XX/24.
6) Kuchli tomonlar.
7) Eng muhim 5 ta tuzatish.
8) 30-60 soniyalik ovozli tahlil uchun ravon o'zbekcha skript.

ESSE:
{essay}"""
    r = client.responses.create(model="gpt-5", input=prompt)
    return r.output_text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Hojimurod Esse Botga xush kelibsiz.\n"
        "Esse matnini yoki ovozli xabarni yuboring. Men 12 kriteriy bo'yicha 24 ballik tahlil qilaman."
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Esse qabul qilindi. 12 kriteriy bo'yicha tekshiryapman...")
    try:
        result = await asyncio.to_thread(analyze, update.message.text)
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i+4000])
    except Exception as e:
        await update.message.reply_text("Xatolik: API kalitlari yoki bot sozlamalarini tekshiring.")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ovoz qabul qilindi. Avval matnga aylantiraman, keyin tekshiraman...")
    try:
        f = await update.message.voice.get_file()
        path = "/tmp/essay_voice.ogg"
        await f.download_to_drive(path)
        with open(path, "rb") as audio:
            tr = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe", file=audio, language="uz"
            )
        result = await asyncio.to_thread(analyze, tr.text)
        await update.message.reply_text("🎙 Matnga aylantirildi:\n" + tr.text[:3500])
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i+4000])
    except Exception:
        await update.message.reply_text("Ovozli tahlilda xatolik yuz berdi.")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.add_handler(MessageHandler(filters.VOICE, voice_handler))
app.run_polling()
