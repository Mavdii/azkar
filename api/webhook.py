from fastapi import FastAPI, Request, BackgroundTasks
import os
import asyncio
import aiohttp
from azkar_service import load_active_groups, save_active_groups, load_azkar_texts, send_message

app = FastAPI()


@app.post('/')
async def telegram_webhook(req: Request, background_tasks: BackgroundTasks):
    payload = await req.json()
    # Minimal support: record groups when bot is added in a group via service messages
    try:
        if 'message' in payload:
            msg = payload['message']
            chat = msg.get('chat', {})
            chat_id = chat.get('id')
            chat_type = chat.get('type')
            # only persist groups
            if chat_type in ('group', 'supergroup') and chat_id:
                groups = set(load_active_groups())
                if int(chat_id) not in groups:
                    groups.add(int(chat_id))
                    save_active_groups(list(groups))
    except Exception:
        pass
    return {'ok': True}


# Vercel serverless handler compatibility
async def _handle_request_body(body: dict):
    # reuse same logic as webhook
    try:
        if 'message' in body:
            msg = body['message']
            chat = msg.get('chat', {})
            chat_id = chat.get('id')
            chat_type = chat.get('type')
            if chat_type in ('group', 'supergroup') and chat_id:
                groups = set(load_active_groups())
                if int(chat_id) not in groups:
                    groups.add(int(chat_id))
                    save_active_groups(list(groups))
    except Exception:
        pass
    return {'ok': True}


def handler(request):
    # Vercel calls the module; request body is raw JSON string in environment for python runtime
    try:
        body = request.get_json() if hasattr(request, 'get_json') else request
    except Exception:
        body = {}
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(_handle_request_body(body))
