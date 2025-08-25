
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

async def keep_alive():
    """وظيفة للحفاظ على عمل البوت"""
    while True:
        try:
            # طباعة رسالة كل 30 دقيقة للتأكد من أن البوت يعمل
            logger.info(f"البوت يعمل - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(1800)  # 30 دقيقة
        except Exception as e:
            logger.error(f"خطأ في keep_alive: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(keep_alive())
