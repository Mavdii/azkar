# بوت الأذكار الإسلامية

## متطلبات التشغيل:
1. Python 3.11+
2. تثبيت المكتبات: pip install -r requirements.txt أو استخدام pyproject.toml

## ملفات المشروع:
- main.py: الملف الرئيسي للبوت
- Azkar.txt: نصوص الأذكار (مفصولة بـ ---)
- active_groups.json: المجموعات النشطة المحفوظة
- pyproject.toml: إعدادات المشروع والمكتبات المطلوبة

## المجلدات:
- random/: الصور العشوائية
- voices/: الرسائل الصوتية  
- audios/: الملفات الصوتية
- morning/: صور أذكار الصباح
- evening/: صور أذكار المساء
- prayers/: صور أذكار ما بعد الصلاة

## تشغيل البوت:
python main.py

## ملاحظات:
- تأكد من تعديل bot_token في main.py
- تأكد من تعديل admin_id في main.py
- البوت يحفظ المجموعات تلقائياً ويعود إليها عند إعادة التشغيل

## نشر على Render / Heroku / Docker

باختصار: يمكنك تشغيل البوت كخدمة طويلة الأمد باستخدام Docker أو على Render/Heroku.

1) بناء صورة Docker وتشغيل محلياً:
```bash
docker build -t azkar-bot .
docker run -e BOT_TOKEN="$BOT_TOKEN" -e ADMIN_ID="$ADMIN_ID" azkar-bot
```

2) باستخدام docker-compose:
```bash
BOT_TOKEN=xxx ADMIN_ID=yyy docker-compose up --build
```

3) نشر على Render/Heroku:
 - ادفع المشروع إلى GitHub
 - أنشئ خدمة Web على Render أو تطبيق على Heroku وأشر إلى المستودع
 - اضبط متغيرات البيئة (BOT_TOKEN, ADMIN_ID)
 - اضبط Command إذا لزم: `python main.py`

