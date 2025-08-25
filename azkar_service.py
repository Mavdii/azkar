import os
import json
import random
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Tuple, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    _HAS_BOTO = True
except Exception:
    _HAS_BOTO = False

PROJECT_ROOT = os.path.dirname(__file__)
GROUPS_FILE = os.path.join(PROJECT_ROOT, 'active_groups.json')


def _use_s3():
    return _HAS_BOTO and os.getenv('S3_BUCKET') and os.getenv('AWS_ACCESS_KEY_ID')


def load_active_groups() -> List[int]:
    """Load active groups from S3 if configured, otherwise local file. Returns list of ints."""
    if _use_s3():
        s3 = boto3.client('s3')
        bucket = os.getenv('S3_BUCKET')
        key = os.getenv('S3_KEY', 'active_groups.json')
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
            data = obj['Body'].read()
            decoded = json.loads(data.decode('utf-8'))
            return [int(x) for x in decoded.get('groups', [])]
        except ClientError:
            return []
        except Exception:
            return []

    # local fallback
    try:
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [int(x) for x in data.get('groups', [])]
    except Exception:
        return []
    return []


def save_active_groups(groups: List[int]):
    data = {'groups': groups, 'last_updated': datetime.utcnow().isoformat()}
    if _use_s3():
        s3 = boto3.client('s3')
        bucket = os.getenv('S3_BUCKET')
        key = os.getenv('S3_KEY', 'active_groups.json')
        s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, ensure_ascii=False).encode('utf-8'))
        return

    try:
        with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_azkar_texts() -> List[str]:
    path = os.path.join(PROJECT_ROOT, 'Azkar.txt')
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                azkar_list = [azkar.strip() for azkar in content.split('---') if azkar.strip()]
                return azkar_list or ["سبحان الله وبحمده"]
    except Exception:
        return ["سبحان الله وبحمده"]
    return ["سبحان الله وبحمده"]


def get_random_file(folder: str, extensions: Tuple[str, ...]) -> Tuple[Optional[str], Optional[str]]:
    try:
        full = os.path.join(PROJECT_ROOT, folder)
        if os.path.exists(full):
            files = [f for f in os.listdir(full) if f.lower().endswith(extensions) and not f.endswith('.info')]
            if files:
                selected = random.choice(files)
                path = os.path.join(full, selected)
                info_path = f"{path}.info"
                caption = None
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            user_caption = info.get('caption', '').strip()
                            if user_caption:
                                caption = f"**{user_caption}**"
                    except Exception:
                        pass
                return path, caption
    except Exception:
        pass
    return None, None


async def send_message(session: aiohttp.ClientSession, bot_token: str, chat_id: int, text: str, reply_markup: dict = None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup, ensure_ascii=False)
    async with session.post(url, data=data, timeout=30) as resp:
        try:
            return await resp.json()
        except Exception:
            return {'ok': False}


async def send_file(session: aiohttp.ClientSession, bot_token: str, method: str, chat_id: int, file_path: str, caption: str = None, field_name: str = 'photo', reply_markup: dict = None):
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    data = aiohttp.FormData()
    data.add_field('chat_id', str(chat_id))
    if caption:
        data.add_field('caption', caption)
        data.add_field('parse_mode', 'Markdown')
    if reply_markup:
        data.add_field('reply_markup', json.dumps(reply_markup, ensure_ascii=False))

    try:
        with open(file_path, 'rb') as f:
            data.add_field(field_name, f, filename=os.path.basename(file_path))
            async with session.post(url, data=data, timeout=60) as resp:
                try:
                    return await resp.json()
                except Exception:
                    return {'ok': False}
    except Exception:
        return {'ok': False}
