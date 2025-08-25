import os
import asyncio
import aiohttp
from azkar_service import load_active_groups, send_message


async def send_prayer_to_all(message_text: str):
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        return {'ok': False, 'error': 'BOT_TOKEN not set'}

    groups = load_active_groups()
    if not groups:
        return {'ok': True, 'sent': 0}

    async with aiohttp.ClientSession() as session:
        sent = 0
        for gid in groups:
            try:
                await send_message(session, bot_token, gid, message_text)
                sent += 1
            except Exception:
                pass
        return {'ok': True, 'sent': sent}


def handler(request):
    # Example text can be passed via env or defaults
    text = os.getenv('PRAYER_MESSAGE', 'وقت الصلاة، تذكروا الصلاة')
    loop = asyncio.new_event_loop()
    res = loop.run_until_complete(send_prayer_to_all(text))
    return res
