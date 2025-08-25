from fastapi import FastAPI, Request, BackgroundTasks, Response
import os
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


@app.get('/favicon.ico')
async def favicon():
    # Return empty response for favicon requests to reduce logs
    return Response(status_code=204)


# NOTE:
# Removed module-level `handler` and helper coroutine that caused Vercel runtime
# to treat a non-class object as an HTTP handler and call issubclass() on it.
# Vercel will now detect `app` (FastAPI instance) and run it as an ASGI app.
