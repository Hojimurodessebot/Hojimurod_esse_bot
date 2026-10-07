import os
import asyncio
import base64
import json

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from openai import OpenAI


# =========================
# SOZLAMALAR
# =========================

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================
# RASMIY BAHOLASH MEZONI
# =========================

RUBRIC = """

SEN ONA TILI VA ADABIYOT FANIDAN MILLIY SERTIFIKAT
ESSESINI TEKSHIRUVCHI TAJRIBALI EKSPERTSAN.

Baholash 12 ta mezon bo‘yicha amalga oshiriladi.

HAR BIR MEZON FAQAT:
0
0.5
1
1.5
2
ball bilan baholanadi.

JAMI MAKSIMAL BALL: 24.

MUHIM:
Ballni taxminan qo‘yma.
Har bir qo‘yilgan ball uchun essedan aniq dalil top.
Agar dalil bo‘lmasa, yuqori ball bermagin.

=========================
MAXSUS HOLATLAR
=========================

1. Esse umuman yozilmagan bo‘lsa — 0 ball.
2. Esse yozilgan, lekin mavzuga mos bo‘lmasa — 2 ball.
3. Esse hajmi 100 so‘zdan kam bo‘lsa — 2 ball.
4. Esse boshqa manbadan ko‘chirilgan bo‘lsa — 2 ball.

Bu maxsus holatlardan biri mavjud bo‘lsa,
avval shu holatni aniqlab yoz.

=========================
1-MEZON
TOPSHIRIQ TALABLARINING BAJARILGANLIGI
=========================

2 ball:
Esse to‘liq publitsistik uslubda yozilgan.

1.5 ball:
Ayrim o‘rinlarda publitsistik uslubdan chekinilgan.

1 ball:
Esse qisman publitsistik uslubda yozilgan.

0.5 ball:
Esse to‘liq badiiy uslubda yozilgan.

0 ball:
Esse to‘liq so‘zlashuv uslubida yozilgan.

Uslubni baholaganda:
- publitsistik uslub;
- badiiy uslub;
- so‘zlashuv uslubi
elementlarini ajrat.

=========================
2-MEZON
IKKI QARASH VA SHAXSIY QARASH
=========================

2 ball:
Vaziyat yuzasidan har ikkala qarash hamda
talabgorning shaxsiy qarashi to‘liq yoritilgan.

1.5 ball:
Har ikkala qarash yoritilgan,
lekin shaxsiy fikr yoritilmagan.

1 ball:
Qarashlarning bittasi to‘liq yoritilgan.

0.5 ball:
Faqat bitta qarash qisman yoritilgan.

0 ball:
Vaziyat yuzasidan qarashlar yoritilmagan.

MUHIM:
Shunchaki "menimcha" degan jumla mavjudligi
shaxsiy qarash yetarli degani emas.
Shaxsiy pozitsiya mazmunan aniq bo‘lishi kerak.

=========================
3-MEZON
DALILLASH
=========================

Har ikkala qarash dalillar bilan asoslanganmi,
tekshir.

2 ball:
Har ikkala qarash dalillar bilan asoslangan.

1.5 ball:
Har ikkala qarash uchun dalillar mavjud,
lekin ayrim dalillar yetarli darajada asoslanmagan.

1 ball:
Faqat bitta qarash dalillangan.

0.5 ball:
Har ikkala qarash uchun dalil keltirilgan,
lekin dalillar juda zaif yoki yuzaki.

0 ball:
Har ikkala qarash dalillanmagan.

Dalil sifatida:
- hayotiy misol;
- aniq fakt;
- sabab-oqibat;
- statistik yoki ijtimoiy dalil;
- real kuzatuv
kabi asoslarni hisobga ol.

Oddiy fikrni dalil deb hisoblama.

=========================
4-MEZON
MATN YAXLITLIGI
=========================

Kirish → asosiy qism → xulosa
tuzilishini tekshir.

Qismlar bir-biri bilan mazmunan bog‘langan bo‘lishi kerak.

=========================
5-MEZON
MANTIQIY QURILISH VA BOG‘LIQLIK
=========================

Gaplar, fikrlar va abzatslar o‘rtasidagi
mantiqiy bog‘lanishni tekshir.

Fikr bir joydan ikkinchi joyga keskin sakramasligi kerak.

=========================
6-MEZON
FIKRLARNING TAHLILI VA MANTIQIY IZCHILLIK
=========================

Muallif faqat fikr bildirganmi yoki
fikrni tahlil qilganmi?

Sabab → oqibat → izoh → xulosa
aloqalarini tekshir.

Bir xil fikrni takrorlashni tahlil deb hisoblama.

=========================
7-MEZON
IMLO
=========================

Faqat haqiqiy imlo xatolarini sanash.

Har bir xato uchun:

XATO:
"..."

TO‘G‘RISI:
"..."

SABAB:
qaysi imlo qoidasi buzilgan.

Bir xil xatoni bir necha marta takrorlab,
sun’iy ravishda ballni pasaytirma.

=========================
8-MEZON
PUNKTUATSIYA
=========================

Vergul, nuqta, ikki nuqta, nuqtali vergul,
tire, qo‘shtirnoq va boshqa tinish belgilarini tekshir.

Har bir xatoni aniq ko‘rsat.

=========================
9-MEZON
SO‘Z QO‘LLASH BILAN BOG‘LIQ XATOLAR
=========================

Quyidagilarni tekshir:

- noto‘g‘ri so‘z tanlash;
- so‘zning ma’nosini noto‘g‘ri qo‘llash;
- noo‘rin takror;
- ortiqcha so‘z;
- tushirib qoldirilgan so‘z;
- bog‘lovchi bilan bog‘liq xato;
- kirish so‘z va birikmalarni noo‘rin qo‘llash.

=========================
10-MEZON
USLUBIY YAXLITLIK
=========================

Matnning umumiy uslubiy yaxlitligini tekshir.

Publitsistik esse ichida:
- ortiqcha so‘zlashuv;
- badiiy tasvirning noo‘rin ko‘pligi;
- rasmiy uslubning noo‘rin aralashuvi;
- parazit birliklar
bor-yo‘qligini aniqlash.

=========================
11-MEZON
LUG‘AT BOYLIGI VA LEKSIK XILMA-XILLIK
=========================

Bir xil so‘zlarning ortiqcha takrorlanishini,
sinonimlardan foydalanishni,
so‘z boyligini,
fikrni turli leksik vositalar bilan ifodalashni tekshir.

Faqat uzun yozilgani uchun yuqori ball bermagin.

=========================
12-MEZON
KERAKSIZ BIRLIKLAR
=========================

Quyidagilarni tekshir:

- sheva;
- vulgarizm;
- varvarizm;
- parazit so‘zlar;
- keraksiz takrorlar;
- mazmunga xizmat qilmaydigan birliklar.

=========================
ASOSIY EKSPERT QOIDALARI
=========================

1. Har bir mezon mustaqil baholanadi.
2. Bir xato ikki xil mezonda asossiz ravishda takroriy
jazolanmasin.
3. Yuqori ball berish uchun matndan dalil bo‘lsin.
4. "Yaxshi yozilgan" degan umumiy taassurot asosida ball qo‘yma.
5. Avval dalilni top, keyin ball qo‘y.
6. Ball faqat 0 / 0.5 / 1 / 1.5 / 2 bo‘lishi mumkin.
7. Jami ball 24 dan oshmasin.
8. Matnda mavjud bo‘lmagan xatoni o‘ylab topma.
9. Qo‘lyozma rasm bo‘lsa, noaniq so‘zni xato deb hisoblama.
10. O‘qilishi noaniq joylarni alohida belgila.
"""


# =========================
# MATN TAHLILI
# =========================

def analyze_text(essay):

    prompt = f"""
{RUBRIC}

Quyidagi esseni xuddi fan eksperti kabi tekshir.

ESSE:
----------------
{essay}
----------------

JAVOBNI FAQAT QUYIDAGI TARTIBDA BER:

# 1. ESSE HAQIDA
- So‘zlar soni:
- Mavzuga mosligi:
- Maxsus holat mavjudmi:
- Umumiy xulosa:

# 2. 12 MEZON BO‘YICHA BAHO

Har bir mezon uchun:

MEZON:
BALL:
DALIL:
IZOH:

1. Topshiriq talablarining bajarilganligi
2. Ikki qarash va shaxsiy qarash
3. Dalillash
4. Matn yaxlitligi
5. Mantiqiy qurilish va bog‘liqlik
6. Fikrlarning tahlili va mantiqiy izchillik
7. Imlo
8. Punktuatsiya
9. So‘z qo‘llash bilan bog‘liq xatolar
10. Uslubiy yaxlitlik
11. Lug‘at boyligi va leksik xilma-xillik
12. Keraksiz/sheva/vulgarizm/varvarizm/parazit birliklar

# 3. IMLO XATOLARI

Har birini:

1) Xato:
   To‘g‘risi:
   Izoh:

Agar xato bo‘lmasa:
"Imlo xatosi aniqlanmadi."

# 4. PUNKTUATSIYA XATOLARI

Har birini aniq ko‘rsat.

# 5. USLUBIY XATOLAR

Har birini aniq ko‘rsat.

# 6. LUG‘AVIY XATOLAR

Har birini aniq ko‘rsat.

# 7. JAMI

XX / 24

# 8. KUCHLI TOMONLAR

Kamida 3 ta.

# 9. ENG MUHIM 5 TA TUZATISH

O‘quvchi birinchi navbatda nimalarni tuzatishi kerakligini yoz.

# 10. EKSPERT XULOSASI

O‘quvchining esse yozish darajasini qisqa va xolis bahola.
"""


    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )

    return response.output_text


# =========================
# RASMNI TAHLIL QILISH
# =========================

def analyze_image(image_path):

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""
{RUBRIC}

Bu rasmda qo‘lyozma esse mavjud.

1. Avval esseni imkon qadar TO‘LIQ o‘qib, matnga aylantir.
2. O‘qilishi noaniq joyni o‘ylab topma.
3. Keyin esseni yuqoridagi rasmiy mezonlar asosida tekshir.
4. Har bir ball uchun aniq dalil keltir.

Natija:

# 1. KO‘CHIRIB YOZILGAN MATN

Esse matnini imkon qadar to‘liq yoz.

# 2. SO‘ZLAR SONI

# 3. 12 MEZON BO‘YICHA BAHO

Har bir mezon:
- ball
- dalil
- ekspert izohi

# 4. IMLO XATOLARI

# 5. PUNKTUATSIYA XATOLARI

# 6. USLUBIY XATOLAR

# 7. LUG‘AVIY XATOLAR

# 8. JAMI BALL

XX / 24

# 9. EKSPERT XULOSASI
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
                        "image_url": f"data:image/jpeg;base64,{encoded}",
                        "detail": "high"
                    }
                ]
            }
        ]
    )

    return response.output_text


# =========================
# UZUN JAVOBNI BO‘LIB YUBORISH
# =========================

async def send_long_message(message, text):

    limit = 3900

    for i in range(0, len(text), limit):
        await message.reply_text(text[i:i + limit])


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\n"
        "Hojimurod Esse Bot ishga tayyor.\n\n"
        "📝 Esse matnini yuboring.\n"
        "📷 Qo‘lyozma esse rasmini yuboring.\n"
        "🎙 Ovozli esse yuborishingiz ham mumkin.\n\n"
        "Men esseni 12 mezon bo‘yicha 24 ballik tizimda "
        "ekspert usulida tahlil qilaman."
    )


# =========================
# MATN
# =========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📝 Esse qabul qilindi.\n\n"
        "12 ta mezon bo‘yicha ekspert tahlili boshlanmoqda..."
    )

    try:

        result = await asyncio.to_thread(
            analyze_text,
            update.message.text
        )

        await send_long_message(
            update.message,
            result
        )

    except Exception as e:

        print("TEXT ERROR:", e)

        await update.message.reply_text(
            "❌ Tahlilda xatolik yuz berdi."
        )


# =========================
# RASM
# =========================

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📷 Rasm qabul qilindi.\n\n"
        "Avval qo‘lyozmani o‘qiyapman, "
        "keyin 12 mezon bo‘yicha ekspert tahlil qilaman..."
    )

    try:

        photo = update.message.photo[-1]

        file = await photo.get_file()

        path = "/tmp/essay.jpg"

        await file.download_to_drive(path)

        result = await asyncio.to_thread(
            analyze_image,
            path
        )

        await send_long_message(
            update.message,
            result
        )

    except Exception as e:

        print("PHOTO ERROR:", e)

        await update.message.reply_text(
            "❌ Rasmni tahlil qilishda xatolik yuz berdi."
        )


# =========================
# OVOZ
# =========================

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎙 Ovoz qabul qilindi.\n\n"
        "Avval matnga aylantiraman, "
        "keyin ekspert mezonlari bo‘yicha tekshiraman..."
    )

    try:

        voice_file = await update.message.voice.get_file()

        path = "/tmp/essay_voice.ogg"

        await voice_file.download_to_drive(path)

        with open(path, "rb") as audio:

            transcription = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio,
                language="uz"
            )

        text = transcription.text

        await update.message.reply_text(
            "🎙 Matnga aylantirilgan esse:\n\n"
            + text[:3500]
        )

        result = await asyncio.to_thread(
            analyze_text,
            text
        )

        await send_long_message(
            update.message,
            result
        )

    except Exception as e:

        print("VOICE ERROR:", e)

        await update.message.reply_text(
            "❌ Ovozli tahlilda xatolik yuz berdi."
        )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        photo_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.VOICE,
        voice_handler
    )
)

print("BOT ISHLAYAPTI...")

app.run_polling()
