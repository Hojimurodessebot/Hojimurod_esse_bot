# Esse Tekshiruvchi Telegram Bot

Bu bot Ona tili va adabiyot esselarini 12 kriteriya bo‘yicha, jami 24 ballik tizimda tekshiradi.

## Imkoniyatlar
- Matn ko‘rinishidagi esseni tekshiradi.
- Telegram voice/audio yuborilsa, avval matnga o‘giradi.
- 12 kriteriyaning har biriga 0 / 0.5 / 1 / 1.5 / 2 ball beradi.
- Har bir kriteriya bo‘yicha dalil, topilgan xato va tavsiya beradi.
- Yakunda 24 ballik natija chiqaradi.
- Natijani ovozli javob sifatida ham yuboradi.

## Ishga tushirish
1. Python 3.11+ o‘rnating.
2. FFmpeg o‘rnating va PATH ga qo‘shing.
3. `.env.example` faylidan `.env` yarating.
4. Telegram @BotFather orqali bot token oling.
5. OpenAI API kalitini `.env` ga kiriting.
6. `pip install -r requirements.txt`
7. `python bot.py`

## Muhim
Bot mezonlarni avtomatik o‘zgartirmaydi. `PROMPT` ichidagi 12 kriteriya qoidalari asosida baholaydi.
AI bahosi yordamchi ekspert tizimi hisoblanadi; rasmiy imtihon natijasining kafolati emas.
