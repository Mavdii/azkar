def handler(request):
    return {"ok": True, "service": "azkar-bot", "time": __import__('datetime').datetime.utcnow().isoformat()}
