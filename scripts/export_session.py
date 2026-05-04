"""
Le a sessao Telethon local (arena_listener.session) e imprime como
StringSession, pra colar no Railway/qualquer host como variavel de
ambiente STRING_SESSION.

Rode UMA VEZ depois de ter feito login local:
    .venv\\Scripts\\python.exe scripts\\export_session.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_name = os.environ.get("SESSION_NAME", "arena_listener")

with TelegramClient(session_name, api_id, api_hash) as client:
    s = StringSession.save(client.session)

print()
print("=" * 70)
print("STRING_SESSION (cole no Railway como variavel de ambiente):")
print("=" * 70)
print(s)
print("=" * 70)
print()
print("ATENCAO: essa string da acesso TOTAL a sua conta Telegram.")
print("Trate como senha. Nao commite, nao compartilhe em chat.")
