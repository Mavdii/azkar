import os
import random
import asyncio
import logging
from datetime import datetime, timedelta
import pytz
import json
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import signal
import sys

# إعداد نظام السجلات المحسن
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class AzkarBot:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN", "7732686950:AAGDC3iAlhPqlkGhakPYEqFwr_chK97DCgI")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.admin_id = int(os.getenv("ADMIN_ID", "7089656746"))

        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Africa/Cairo'))
        self.cairo_tz = pytz.timezone('Africa/Cairo')
        self.active_groups = set()
        self.last_message_ids = {}
        self.content_turn = 0
        self.offset = 0
        self.session = None
        self.is_running = True

        # ملفات التكوين
        self.groups_file = 'active_groups.json'
        self.channel_link = "https://t.me/Telawat_Quran_0"
        self.admin_states = {}

        # إنشاء المجلدات وتحميل البيانات
        self.ensure_directories()
        self.load_active_groups()
        self.create_default_content()

    def ensure_directories(self):
        """إنشاء المجلدات المطلوبة مع معالجة الأخطاء"""
        directories = ['random', 'morning', 'evening', 'prayers', 'voices', 'audios']
        for directory in directories:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    # إنشاء ملف placeholder إذا لم يوجد
                    placeholder_file = os.path.join(directory, 'placeholder.txt')
                    if not os.path.exists(placeholder_file):
                        with open(placeholder_file, 'w', encoding='utf-8') as f:
                            f.write(f"placeholder for {directory} folder")
                    logger.info(f"تم إنشاء مجلد: {directory}")
            except Exception as e:
                logger.error(f"خطأ في إنشاء المجلد {directory}: {e}")

    def create_default_content(self):
        """إنشاء محتوى افتراضي إذا لم يوجد"""
        try:
            if not os.path.exists('Azkar.txt'):
                default_azkar = """سبحان الله وبحمده، سبحان الله العظيم
---
لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير
---
اللهم صل وسلم على نبينا محمد
---
أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه
---
لا حول ولا قوة إلا بالله العلي العظيم
---
سبحان الله والحمد لله ولا إله إلا الله والله أكبر
---
اللهم أعني على ذكرك وشكرك وحسن عبادتك"""

                with open('Azkar.txt', 'w', encoding='utf-8') as f:
                    f.write(default_azkar)
                logger.info("تم إنشاء ملف الأذكار الافتراضي")
        except Exception as e:
            logger.error(f"خطأ في إنشاء المحتوى الافتراضي: {e}")

    def save_active_groups(self):
        """حفظ المجموعات النشطة مع معالجة الأخطاء"""
        try:
            groups_data = {
                'groups': list(self.active_groups),
                'last_updated': datetime.now(self.cairo_tz).isoformat()
            }
            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump(groups_data, f, ensure_ascii=False, indent=2)
            logger.info(f"تم حفظ {len(self.active_groups)} مجموعة نشطة")
        except Exception as e:
            logger.error(f"خطأ في حفظ المجموعات: {e}")

    def load_active_groups(self):
        """تحميل المجموعات النشطة مع معالجة الأخطاء"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved_groups = data.get('groups', [])
                    # التأكد من أن جميع العناصر أرقام صحيحة
                    self.active_groups = set(int(group) for group in saved_groups if str(group).lstrip('-').isdigit())
                    logger.info(f"تم تحميل {len(self.active_groups)} مجموعة نشطة")
            else:
                self.active_groups = set()
                logger.info("لا يوجد ملف مجموعات محفوظ")
        except Exception as e:
            logger.error(f"خطأ في تحميل المجموعات: {e}")
            self.active_groups = set()

    async def start_bot(self):
        """تشغيل البوت مع معالجة شاملة للأخطاء"""
        logger.info("🚀 بدء تشغيل بوت الأذكار الإسلامية على Replit...")

        # إعداد معالج الإشارات
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            # إنشاء جلسة HTTP مع إعدادات محسنة
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )

            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'Azkar Bot/1.0'}
            )

            # التحقق من صحة التوكن
            if not await self.test_bot_token():
                logger.error("❌ توكن البوت غير صحيح")
                return

            # بدء الجدولة
            await self.setup_scheduler()

            # جدولة المهام اليومية
            await self.schedule_prayer_notifications()

            logger.info(f"✅ البوت يعمل الآن مع {len(self.active_groups)} مجموعة نشطة")

            # بدء معالجة الرسائل
            await self.process_updates()

        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
            raise
        finally:
            await self.cleanup()

    def signal_handler(self, signum, frame):
        """معالج إشارات الإيقاف"""
        logger.info(f"تم استقبال إشارة الإيقاف: {signum}")
        self.is_running = False

    async def test_bot_token(self):
        """اختبار صحة توكن البوت"""
        try:
            url = f"{self.base_url}/getMe"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data['result']
                        logger.info(f"✅ البوت متصل: @{bot_info.get('username', 'unknown')}")
                        return True
                else:
                    logger.error(f"خطأ في التحقق من التوكن: {response.status}")
        except Exception as e:
            logger.error(f"خطأ في اختبار التوكن: {e}")
        return False

    async def setup_scheduler(self):
        """إعداد الجدولة مع معالجة الأخطاء"""
        try:
            # بدء الجدولة
            self.scheduler.start()

            # أذكار عشوائية كل 5 دقائق
            self.scheduler.add_job(
                self.send_random_content,
                'interval',
                minutes=5,
                timezone=self.cairo_tz,
                id='random_azkar',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=60
            )

            # إرسال المحتوى الأول بعد 30 ثانية
            self.scheduler.add_job(
                self.send_random_content,
                'date',
                run_date=datetime.now(self.cairo_tz) + timedelta(seconds=30),
                timezone=self.cairo_tz,
                id='first_content',
                replace_existing=True
            )

            # أذكار الصباح - مواقيت متعددة
            morning_times = [(5, 30), (7, 0), (8, 0)]
            for i, (hour, minute) in enumerate(morning_times):
                self.scheduler.add_job(
                    self.send_morning_azkar,
                    'cron',
                    hour=hour,
                    minute=minute,
                    timezone=self.cairo_tz,
                    id=f'morning_azkar_{i}',
                    replace_existing=True,
                    misfire_grace_time=300
                )

            # أذكار المساء - مواقيت متعددة
            evening_times = [18, 19, 20]
            for i, hour in enumerate(evening_times):
                self.scheduler.add_job(
                    self.send_evening_azkar,
                    'cron',
                    hour=hour,
                    minute=0,
                    timezone=self.cairo_tz,
                    id=f'evening_azkar_{i}',
                    replace_existing=True,
                    misfire_grace_time=300
                )

            # جدولة يومية لمواقيت الصلاة
            self.scheduler.add_job(
                self.schedule_prayer_notifications,
                'cron',
                hour=0,
                minute=5,
                timezone=self.cairo_tz,
                id='daily_prayer_schedule',
                replace_existing=True
            )

            logger.info("✅ تم إعداد الجدولة بنجاح")

        except Exception as e:
            logger.error(f"خطأ في إعداد الجدولة: {e}")
            raise

    async def cleanup(self):
        """تنظيف الموارد"""
        try:
            self.is_running = False

            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("تم إيقاف الجدولة")

            if self.session and not self.session.closed:
                await self.session.close()
                logger.info("تم إغلاق جلسة HTTP")

            # حفظ البيانات النهائي
            self.save_active_groups()
            logger.info("تم حفظ البيانات النهائي")

        except Exception as e:
            logger.error(f"خطأ في التنظيف: {e}")

    async def process_updates(self):
        """معالجة التحديثات مع إعادة المحاولة الذكية"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        base_delay = 1

        logger.info("🔄 بدء معالجة الرسائل...")

        while self.is_running:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {
                    'offset': self.offset,
                    'limit': 50,
                    'timeout': 10,
                    'allowed_updates': ['message', 'callback_query']
                }

                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            updates = data.get('result', [])

                            for update in updates:
                                if not self.is_running:
                                    break
                                await self.handle_update(update)
                                self.offset = update['update_id'] + 1

                            consecutive_errors = 0

                        else:
                            logger.error(f"خطأ من Telegram API: {data}")
                            consecutive_errors += 1

                    elif response.status == 409:
                        # Conflict - another instance is running
                        logger.warning("تعارض - هناك نسخة أخرى من البوت تعمل")
                        await asyncio.sleep(10)
                        consecutive_errors += 1

                    else:
                        logger.error(f"HTTP Error: {response.status}")
                        consecutive_errors += 1

            except asyncio.TimeoutError:
                logger.warning("انتهت مهلة الاتصال - إعادة المحاولة...")
                consecutive_errors += 1

            except Exception as e:
                logger.error(f"خطأ في معالجة التحديثات: {e}")
                consecutive_errors += 1

            # إدارة الأخطاء المتتالية
            if consecutive_errors > 0:
                if consecutive_errors >= max_consecutive_errors:
                    delay = min(base_delay * (2 ** consecutive_errors), 60)
                    logger.warning(f"أخطاء متتالية ({consecutive_errors}), انتظار {delay} ثانية...")
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(base_delay)
            else:
                await asyncio.sleep(1)

        logger.info("تم إيقاف معالجة الرسائل")

    async def handle_update(self, update):
        """معالجة تحديث واحد مع معالجة شاملة للأخطاء"""
        try:
            if 'message' in update:
                await self.handle_message(update['message'])
            elif 'callback_query' in update:
                await self.handle_callback_query(update['callback_query'])
        except Exception as e:
            logger.error(f"خطأ في معالجة التحديث: {e}")

    async def handle_message(self, message):
        """معالجة الرسائل"""
        try:
            chat = message.get('chat', {})
            chat_id = chat['id']
            text = message.get('text', '')
            user_id = message.get('from', {}).get('id')

            # تسجيل المجموعات تلقائياً
            if chat.get('type') in ['group', 'supergroup']:
                if chat_id not in self.active_groups:
                    self.active_groups.add(chat_id)
                    self.save_active_groups()
                    logger.info(f"مجموعة جديدة: {chat_id}")
                    await self.send_welcome_to_new_group(chat_id)

            # معالجة أوامر المطور
            if user_id == self.admin_id:
                if user_id in self.admin_states:
                    await self.handle_admin_state(message)
                    return

                if text == '/admin':
                    await self.show_admin_panel(chat_id)
                    return

                if message.get('photo') or message.get('voice') or message.get('audio') or message.get('document'):
                    await self.handle_admin_media(message)
                    return

            # أمر البداية
            if text == '/start':
                await self.send_start_message(chat_id)

        except Exception as e:
            logger.error(f"خطأ في معالجة الرسالة: {e}")

    async def get_prayer_times(self):
        """جلب مواقيت الصلاة مع إعادة المحاولة"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                today = datetime.now(self.cairo_tz).strftime('%d-%m-%Y')
                url = f"https://api.aladhan.com/v1/timingsByCity/{today}"
                params = {
                    'city': 'cairo',
                    'country': 'egypt',
                    'method': '8'
                }

                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 200:
                            timings = data['data']['timings']
                            return {
                                'Fajr': timings['Fajr'],
                                'Dhuhr': timings['Dhuhr'],
                                'Asr': timings['Asr'],
                                'Maghrib': timings['Maghrib'],
                                'Isha': timings['Isha']
                            }

            except Exception as e:
                logger.error(f"خطأ في جلب مواقيت الصلاة (محاولة {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None

    async def schedule_prayer_notifications(self):
        """جدولة تنبيهات الصلاة المحسنة"""
        try:
            prayer_times = await self.get_prayer_times()
            if not prayer_times:
                logger.error("فشل في الحصول على مواقيت الصلاة")
                return

            # إزالة المهام القديمة
            current_jobs = self.scheduler.get_jobs()
            for job in current_jobs:
                if 'prayer' in job.id and 'daily' not in job.id:
                    try:
                        self.scheduler.remove_job(job.id)
                    except:
                        pass

            prayer_messages = {
                'Fajr': """🌅 **تنبيه صلاة الفجر** 🌅

⏰ **خمس دقائق على الأذان**

🕌 **لا تنس الوضوء والاستعداد للصلاة**""",

                'Dhuhr': """☀️ **تنبيه صلاة الظهر** ☀️

⏰ **خمس دقائق على الأذان**

🕌 **توقف قليلاً واستعد للصلاة**""",

                'Asr': """🌤️ **تنبيه صلاة العصر** 🌤️

⏰ **خمس دقائق على الأذان**

⚠️ **الصلاة الوسطى - لا تفوتها**""",

                'Maghrib': """🌅 **تنبيه صلاة المغرب** 🌅

⏰ **خمس دقائق على الأذان**

🌇 **وقت استجابة الدعاء**""",

                'Isha': """🌙 **تنبيه صلاة العشاء** 🌙

⏰ **خمس دقائق على الأذان**

🌟 **آخر صلاة في اليوم**"""
            }

            current_time = datetime.now(self.cairo_tz)

            for prayer, time_str in prayer_times.items():
                try:
                    prayer_time = datetime.strptime(time_str, '%H:%M').time()
                    prayer_datetime = datetime.combine(current_time.date(), prayer_time)
                    prayer_datetime = self.cairo_tz.localize(prayer_datetime)

                    if prayer_datetime <= current_time:
                        prayer_datetime += timedelta(days=1)

                    # تنبيه قبل 5 دقائق
                    notification_time = prayer_datetime - timedelta(minutes=5)

                    if notification_time > current_time:
                        self.scheduler.add_job(
                            self.send_prayer_notification,
                            'date',
                            run_date=notification_time,
                            args=[prayer_messages[prayer]],
                            id=f"prayer_{prayer}_{current_time.strftime('%Y%m%d')}",
                            replace_existing=True,
                            misfire_grace_time=300
                        )

                        # صورة ما بعد الصلاة
                        after_prayer_time = prayer_datetime + timedelta(minutes=20)
                        self.scheduler.add_job(
                            self.send_after_prayer_image,
                            'date',
                            run_date=after_prayer_time,
                            id=f"after_prayer_{prayer}_{current_time.strftime('%Y%m%d')}",
                            replace_existing=True,
                            misfire_grace_time=300
                        )

                        logger.info(f"جُدولت صلاة {prayer} في {notification_time}")

                except Exception as e:
                    logger.error(f"خطأ في جدولة صلاة {prayer}: {e}")

        except Exception as e:
            logger.error(f"خطأ في جدولة الصلوات: {e}")

    def load_azkar_texts(self):
        """تحميل نصوص الأذكار مع معالجة الأخطاء"""
        try:
            if os.path.exists('Azkar.txt'):
                with open('Azkar.txt', 'r', encoding='utf-8') as file:
                    content = file.read()
                    azkar_list = [azkar.strip() for azkar in content.split('---') if azkar.strip()]
                    return azkar_list if azkar_list else ["سبحان الله وبحمده"]
            else:
                return ["سبحان الله وبحمده", "لا إله إلا الله", "الله أكبر"]
        except Exception as e:
            logger.error(f"خطأ في تحميل الأذكار: {e}")
            return ["سبحان الله وبحمده"]

    def get_random_file(self, folder, extensions):
        """الحصول على ملف عشوائي مع معالجة الأخطاء"""
        try:
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) if f.lower().endswith(extensions) and not f.endswith('.info')]
                if files:
                    selected_file = random.choice(files)
                    file_path = os.path.join(folder, selected_file)

                    # قراءة الوصف
                    info_file = f"{file_path}.info"
                    caption = None

                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                info_data = json.load(f)
                                user_caption = info_data.get('caption', '').strip()
                                if user_caption:
                                    caption = f"**{user_caption}**"
                        except Exception as e:
                            logger.error(f"خطأ في قراءة ملف المعلومات: {e}")

                    return file_path, caption
        except Exception as e:
            logger.error(f"خطأ في قراءة المجلد {folder}: {e}")
        return None, None

    def create_inline_keyboard(self):
        """إنشاء لوحة المفاتيح"""
        return {
            "inline_keyboard": [[{
                "text": "📿 تلاوات قرانية - أجر",
                "url": self.channel_link
            }]]
        }

    def create_start_keyboard(self):
        """لوحة مفاتيح رسالة البداية"""
        return {
            "inline_keyboard": [
                [
                    {"text": "👨‍💻 مطور البوت", "url": "https://t.me/mavdiii"},
                    {"text": "📂 Source code", "url": "https://github.com/Mavdii/bot"}
                ],
                [
                    {"text": "➕ اضافة البوت الى مجموعتك", "url": "https://t.me/Mouslim_alarm_bot?startgroup=inpvbtn"}
                ]
            ]
        }

    async def send_message(self, chat_id, text, reply_markup=None, retry_count=0):
        """إرسال رسالة مع إعادة المحاولة"""
        max_retries = 3

        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)

            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        return result['result']['message_id']
                elif response.status == 403:
                    # البوت محظور في المجموعة
                    if chat_id in self.active_groups:
                        self.active_groups.remove(chat_id)
                        self.save_active_groups()
                        logger.info(f"تم إزالة المجموعة المحظورة: {chat_id}")
                elif response.status == 429 and retry_count < max_retries:
                    # Rate limit
                    await asyncio.sleep(1)
                    return await self.send_message(chat_id, text, reply_markup, retry_count + 1)

        except Exception as e:
            if retry_count < max_retries:
                await asyncio.sleep(1)
                return await self.send_message(chat_id, text, reply_markup, retry_count + 1)
            logger.error(f"خطأ في إرسال الرسالة: {e}")
        return None

    async def send_start_message(self, chat_id):
        """إرسال رسالة البداية"""
        start_text = """**🌿 مرحبًا بك في بوت الأذكار 🌿**

**قال تعالى: "فاذكروني أذكركم واشكروا لي ولا تكفرون"**

**هذا البوت يذكرك بالله ويرسل لك أذكار يومية**

**📌 قم بإضافة البوت الى مجموعتك**"""

        reply_markup = self.create_start_keyboard()
        await self.send_message(chat_id, start_text, reply_markup)

    async def send_welcome_to_new_group(self, chat_id):
        """رسالة ترحيب للمجموعة الجديدة"""
        welcome_text = """🌿 **أهلاً وسهلاً بكم في بوت الأذكار** 🌿

✅ **تم تفعيل البوت بنجاح**

📿 **سيرسل البوت أذكار كل 5 دقائق**

🤲 **بارك الله فيكم**"""

        reply_markup = self.create_inline_keyboard()
        await self.send_message(chat_id, welcome_text, reply_markup)

    async def send_random_content(self):
        """إرسال محتوى عشوائي"""
        if not self.active_groups:
            return

        content_sent = False

        for chat_id in self.active_groups.copy():
            try:
                reply_markup = self.create_inline_keyboard()

                if self.content_turn == 0:
                    # نص
                    azkar_list = self.load_azkar_texts()
                    azkar_text = random.choice(azkar_list)
                    text = f"**{azkar_text}**"
                    await self.send_message(chat_id, text, reply_markup)
                    content_sent = True

                elif self.content_turn == 1:
                    # صورة
                    image_path, caption = self.get_random_file('random', ('.png', '.jpg', '.jpeg'))
                    if image_path:
                        if caption:
                            await self.send_photo(chat_id, image_path, caption, reply_markup)
                        else:
                            await self.send_photo_without_caption(chat_id, image_path, reply_markup)
                        content_sent = True

                elif self.content_turn == 2:
                    # صوت
                    voice_path, caption = self.get_random_file('voices', ('.ogg', '.mp3'))
                    if voice_path:
                        if caption:
                            await self.send_voice(chat_id, voice_path, caption, reply_markup)
                        else:
                            await self.send_voice_without_caption(chat_id, voice_path, reply_markup)
                        content_sent = True

                elif self.content_turn == 3:
                    # ملف صوتي
                    audio_path, caption = self.get_random_file('audios', ('.mp3', '.mp4', '.wav'))
                    if audio_path:
                        if caption:
                            await self.send_audio(chat_id, audio_path, caption, reply_markup)
                        else:
                            await self.send_audio_without_caption(chat_id, audio_path, reply_markup)
                        content_sent = True

                # نص بديل إذا لم يتم إرسال محتوى
                if not content_sent:
                    azkar_list = self.load_azkar_texts()
                    azkar_text = random.choice(azkar_list)
                    text = f"**{azkar_text}**"
                    await self.send_message(chat_id, text, reply_markup)

            except Exception as e:
                logger.error(f"خطأ في إرسال المحتوى للمجموعة {chat_id}: {e}")

        # تحديث دورة المحتوى
        self.content_turn = (self.content_turn + 1) % 4

    async def send_morning_azkar(self):
        """أذكار الصباح"""
        if not self.active_groups:
            return

        for chat_id in self.active_groups.copy():
            try:
                image_path, _ = self.get_random_file('morning', ('.png', '.jpg', '.jpeg'))
                reply_markup = self.create_inline_keyboard()

                if image_path:
                    caption = "🌅 **أذكار الصباح** 🌅"
                    await self.send_photo(chat_id, image_path, caption, reply_markup)
                else:
                    text = "🌅 **لا تنس أذكار الصباح** 🌅"
                    await self.send_message(chat_id, text, reply_markup)

            except Exception as e:
                logger.error(f"خطأ في أذكار الصباح: {e}")

    async def send_evening_azkar(self):
        """أذكار المساء"""
        if not self.active_groups:
            return

        for chat_id in self.active_groups.copy():
            try:
                image_path, _ = self.get_random_file('evening', ('.png', '.jpg', '.jpeg'))
                reply_markup = self.create_inline_keyboard()

                if image_path:
                    caption = "🌇 **أذكار المساء** 🌇"
                    await self.send_photo(chat_id, image_path, caption, reply_markup)
                else:
                    text = "🌇 **لا تنس أذكار المساء** 🌇"
                    await self.send_message(chat_id, text, reply_markup)

            except Exception as e:
                logger.error(f"خطأ في أذكار المساء: {e}")

    async def send_prayer_notification(self, message_text):
        """إرسال تنبيه الصلاة"""
        if not self.active_groups:
            return

        reply_markup = self.create_inline_keyboard()
        for chat_id in self.active_groups.copy():
            try:
                await self.send_message(chat_id, message_text, reply_markup)
            except Exception as e:
                logger.error(f"خطأ في تنبيه الصلاة: {e}")

    async def send_after_prayer_image(self):
        """صورة ما بعد الصلاة"""
        if not self.active_groups:
            return

        for chat_id in self.active_groups.copy():
            try:
                image_path, _ = self.get_random_file('prayers', ('.png', '.jpg', '.jpeg'))
                reply_markup = self.create_inline_keyboard()

                if image_path:
                    caption = "🕌 **أذكار ما بعد الصلاة** 🕌"
                    await self.send_photo(chat_id, image_path, caption, reply_markup)
                else:
                    text = "🕌 **لا تنس أذكار ما بعد الصلاة** 🕌"
                    await self.send_message(chat_id, text, reply_markup)

            except Exception as e:
                logger.error(f"خطأ في صورة ما بعد الصلاة: {e}")

    # باقي الدوال المساعدة للإرسال والإدارة
    async def send_photo(self, chat_id, photo_path, caption, reply_markup=None):
        """إرسال صورة"""
        try:
            url = f"{self.base_url}/sendPhoto"
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))

            with open(photo_path, 'rb') as photo_file:
                data.add_field('photo', photo_file)
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الصورة: {e}")
        return None

    async def send_photo_without_caption(self, chat_id, photo_path, reply_markup=None):
        """إرسال صورة بدون وصف"""
        try:
            url = f"{self.base_url}/sendPhoto"
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))

            with open(photo_path, 'rb') as photo_file:
                data.add_field('photo', photo_file)
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الصورة: {e}")
        return None

    async def send_voice(self, chat_id, voice_path, caption, reply_markup=None):
        """إرسال رسالة صوتية"""
        try:
            url = f"{self.base_url}/sendVoice"
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))

            with open(voice_path, 'rb') as voice_file:
                data.add_field('voice', voice_file)
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الصوت: {e}")
        return None

    async def send_voice_without_caption(self, chat_id, voice_path, reply_markup=None):
        """إرسال صوت بدون وصف"""
        try:
            url = f"{self.base_url}/sendVoice"
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))

            with open(voice_path, 'rb') as voice_file:
                data.add_field('voice', voice_file)
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الصوت: {e}")
        return None

    async def send_audio(self, chat_id, audio_path, caption, reply_markup=None):
        """إرسال ملف صوتي"""
        try:
            url = f"{self.base_url}/sendAudio"
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))

            with open(audio_path, 'rb') as audio_file:
                data.add_field('audio', audio_file)
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الملف الصوتي: {e}")
        return None

    async def send_audio_without_caption(self, chat_id, audio_path, reply_markup=None):
        """إرسال ملف صوتي بدون وصف"""
        try:
            url = f"{self.base_url}/sendAudio"
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            if reply_markup:
                data.add_field('reply_markup', json.dumps(reply_markup))

            with open(audio_path, 'rb') as audio_file:
                data.add_field('audio', audio_file)
                async with self.session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result['result']['message_id']
        except Exception as e:
            logger.error(f"خطأ في إرسال الملف الصوتي: {e}")
        return None

    # باقي دوال الإدارة (مبسطة للتوافق مع Replit)
    async def show_admin_panel(self, chat_id):
        """لوحة تحكم المطور"""
        text = """🔧 **لوحة التحكم** 🔧

✅ البوت يعمل بشكل طبيعي
📊 إحصائيات سريعة"""

        keyboard = {
            "inline_keyboard": [[
                {"text": "📊 الإحصائيات", "callback_data": "admin_stats"}
            ]]
        }
        await self.send_message(chat_id, text, keyboard)

    async def handle_callback_query(self, callback_query):
        """معالجة النقر على الأزرار"""
        user_id = callback_query['from']['id']
        chat_id = callback_query['message']['chat']['id']
        data = callback_query['data']

        if user_id != self.admin_id:
            return

        if data == "admin_stats":
            stats = await self.get_bot_stats()
            await self.send_message(chat_id, stats)

    async def handle_admin_state(self, message):
        """معالجة حالات المطور"""
        pass

    async def handle_admin_media(self, message):
        """معالجة ملفات المطور"""
        pass

    async def get_bot_stats(self):
        """إحصائيات البوت"""
        groups_count = len(self.active_groups)
        texts_count = len(self.load_azkar_texts())

        return f"""📊 **إحصائيات البوت:**

👥 **المجموعات:** {groups_count}
📝 **النصوص:** {texts_count}
⏰ **الوقت:** {datetime.now(self.cairo_tz).strftime('%H:%M')}"""

# تشغيل البوت
async def main():
    """الدالة الرئيسية"""
    bot = AzkarBot()

    try:
        logger.info("🚀 بدء تشغيل البوت على Replit...")
        await bot.start_bot()

    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت يدوياً")

    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")

    finally:
        await bot.cleanup()
        logger.info("🔚 تم إنهاء البوت")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إنهاء البرنامج")
    except Exception as e:
        logger.error(f"خطأ في البرنامج الرئيسي: {e}")