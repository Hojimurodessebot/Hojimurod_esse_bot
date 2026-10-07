import os
import asyncio
import base64

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
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

Har bir kriteriy: 0, 0.5, 1, 1.5 yoki 2 ball.
Jami: 24 ball.
"""


def analyze_text(essay):
    prompt = f"""
Sen O'zbek tili va adabiyoti milliy sertifikat
esse tekshiruvchisisan.

Esse-ni juda aniq va xolis tekshir.

{RUBRIC}

Natijani quyidagi tartibda ber:

1) 12 kriteriy jadvali:
kriteriy | ball | asos | aniq topilmalar

2) Imlo xatolari:
- soni
- har bir xato
- to'g'ri varianti

3) Punktuatsiya xatolari:
- soni
- har bir xato
- to'g'ri varianti

4) Uslubiy va lug'aviy xatolar.

5) Jami: XX/24.

6) Kuchli tomonlar.

7) Eng muhim 5 ta tuzatish.

8) 30-60 soniyalik ovozli tahlil uchun
ravon o'zbekcha skript.

MUHIM:
Agar matn rasm yoki qo'lyozmadan o'qilgan bo'lsa,
o'qilishi noaniq joylarni taxmin qilib yuborma.
Noaniq joyni alohida ko'rsat.

ESSE:
{essay}
"""

    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )

    return response.output_text


def analyze_image(image_bytes):
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:image/jpeg;base64,{encoded}"

    prompt = f"""
Sen O'zbek tili va adabiyoti milliy sertifikat
esse tekshiruvchisisan.

Rasmda qo'lyozma esse bor.

Avval rasmni diqqat bilan o'qib,
essening matnini imkon qadar to'liq aniqlagin.

Keyin shu esse-ni quyidagi 12 kriteriy
bo'yicha 24 ballik tizimda tekshir:

{RUBRIC}

Natijani quyidagi tartibda ber:

1) O'qilgan esse matni.
2) 12 kriteriy jadvali:
kriteriy | ball | asos | aniq topilmalar

3) Imlo xatolari:
- soni
- xato
- to'g'ri varianti

4) Punktuatsiya xatolari:
- soni
- xato
- to'g'ri varianti

5) Uslubiy va lug'aviy xatolar.

6) Jami: XX/24.

7) Kuchli tomonlar.

8) Eng muhim 5 ta tuzatish.

9) 30-60 soniyalik ovozli tahlil uchun
ravon o'zbekcha skript.

MUHIM:
- Qo'lyozmadagi matnni o'zingdan qo'shma.
- O'qilishi noaniq so'zlarni [noaniq] deb belgila.
- Xatolarni imkon qadar essedagi aniq so'zlar bilan ko'rsat.
"""

    response = client.responses.create(
        model="gpt-5",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url,
                        "detail": "high"
                    }
                ]
            }
        ]
    )

    return response.output_text


async def send_long_result(update, result):
    for i in range(0, len(result), 4000):
        await update.message.reply_text(result[i:i + 4000])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Hojimurod Esse Botga xush kelibsiz.\n\n"
        "Esse matnini, qo'lyozma esse rasmini yoki "
        "ovozli xabarni yuboring.\n\n"
        "Men 12 kriteriy bo'yicha 24 ballik tahlil qilaman."
    )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Esse qabul qilindi. Tekshiryapman..."
    )

    try:
        result = await asyncio.to_thread(
            analyze_text,
            update.message.text
        )

        await send_long_result(update, result)

    except Exception as e:
        print("TEXT ERROR:", e)
        await update.message.reply_text(
            "❌ Tahlilda xatolik yuz berdi."
        )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📷 Esse rasmi qabul qilindi.\n\n"
        "✍️ Qo'lyozmani o'qiyapman va "
        "12 kriteriy bo'yicha tekshiryapman..."
    )

    try:
        photo = update.message.photo[-1]

        file = await photo.get_file()

        image_bytes = await file.download_as_bytearray()

        result = await asyncio.to_thread(
            analyze_image,
            bytes(image_bytes)
        )

        await send_long_result(update, result)

    except Exception as e:
        print("PHOTO ERROR:", e)
        await update.message.reply_text(
            "❌ Rasmni tahlil qilishda xatolik yuz berdi."
        )


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙 Ovoz qabul qilindi. "
        "Avval matnga aylantiraman..."
    )

    try:
        f = await update.message.voice.get_file()

        path = "/tmp/essay_voice.ogg"

        await f.download_to_drive(path)

        with open(path, "rb") as audio:
            tr = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio,
                language="uz"
            )

        await update.message.reply_text(
            "📝 Matnga aylantirildi:\n\n"
            + tr.text[:3500]
        )

        result = await asyncio.to_thread(
            analyze_text,
            tr.text
        )

        await send_long_result(update, result)

    except Exception as e:
        print("VOICE ERROR:", e)
        await update.message.reply_text(
            "❌ Ovozli tahlilda xatolik yuz berdi."
        )


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        photo_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.VOICE,
        voice_handler
    )
)

app.run_polling()
        
