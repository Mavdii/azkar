import os
import asyncio
import aiohttp
from azkar_service import load_active_groups, load_azkar_texts, send_message


async def send_random_to_all():
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        return {'ok': False, 'error': 'BOT_TOKEN not set'}

    groups = load_active_groups()
    if not groups:
        return {'ok': True, 'sent': 0}

    async with aiohttp.ClientSession() as session:
        texts = load_azkar_texts()
        text = f"**{texts[0]}**" if texts else "**سبحان الله**"
        sent = 0
        for gid in groups:
            try:
                await send_message(session, bot_token, gid, text)
                sent += 1
            except Exception:
                pass
        return {'ok': True, 'sent': sent}


def handler(request):
    # Vercel python runtime calls the module; return minimal response
    loop = asyncio.new_event_loop()
    res = loop.run_until_complete(send_random_to_all())
    return res
