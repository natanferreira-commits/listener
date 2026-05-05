import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from telethon import events

from utils.link_extractor import extract_urls_from_message, match_house
from utils.sheet_writer import SheetWriter
from utils.telegram_client import build_client, chat_display_name, message_deeplink

ROOT = Path(__file__).parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging():
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(LOGS_DIR / "listener.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    logging.getLogger("telethon").setLevel(logging.WARNING)


logger = logging.getLogger("arena-listener")


def load_config():
    load_dotenv(ROOT / ".env")
    cfg = {
        "api_id": int(os.environ["API_ID"]),
        "api_hash": os.environ["API_HASH"],
        "phone": os.environ.get("TELEGRAM_PHONE", "").strip() or None,
        "target_channel": os.environ.get("TARGET_CHANNEL", "").strip(),
        "creds_path": os.environ.get("GOOGLE_CREDS_PATH", "./credentials.json"),
        "creds_json": os.environ.get("GOOGLE_CREDS_JSON", "").strip() or None,
        "sheet_id": os.environ["SHEET_ID"],
        "tab_links": os.environ.get("SHEET_TAB_LINKS", "Links Nao Trackeados"),
        "tab_repo": os.environ.get("SHEET_TAB_REPO", "Repo de Links"),
        "session_name": os.environ.get("SESSION_NAME", "arena_listener"),
        "string_session": os.environ.get("STRING_SESSION", "").strip() or None,
    }
    return cfg


async def resolve_target(client, target: str):
    if target.startswith("https://t.me/"):
        target = target.replace("https://t.me/", "").strip("/")
    if target.startswith("@"):
        target = target[1:]
    try:
        entity = await client.get_entity(int(target))
    except ValueError:
        entity = await client.get_entity(target)
    return entity


async def list_my_channels(client):
    logger.info("Listando dialogos da conta...")
    async for dialog in client.iter_dialogs():
        if dialog.is_channel or dialog.is_group:
            uname = getattr(dialog.entity, "username", None)
            tag = f"@{uname}" if uname else "(sem username)"
            logger.info("  - %s %s [id=%s]", dialog.name, tag, dialog.id)


async def run():
    cfg = load_config()
    list_only = "--list" in sys.argv

    client = build_client(cfg["api_id"], cfg["api_hash"], cfg["session_name"], cfg["string_session"])
    if cfg["phone"]:
        await client.start(phone=cfg["phone"])
    else:
        await client.start()
    logger.info("Cliente Telegram conectado.")

    if list_only:
        await list_my_channels(client)
        await client.disconnect()
        return

    if not cfg["target_channel"]:
        logger.error("TARGET_CHANNEL vazio no .env. Rode primeiro com --list pra descobrir o canal.")
        await client.disconnect()
        return

    logger.info("Carregando planilha e lista de casas...")
    writer = SheetWriter(cfg["creds_path"], cfg["sheet_id"], cfg["tab_links"], cfg["tab_repo"], creds_json=cfg["creds_json"])
    houses = writer.load_houses()
    logger.info("Casas carregadas: %s", ", ".join(houses.keys()))

    target = await resolve_target(client, cfg["target_channel"])
    target_name = chat_display_name(target)
    logger.info("Escutando canal: %s", target_name)

    @client.on(events.NewMessage(chats=target))
    async def handler(event):
        try:
            text = event.message.message or ""
            urls = extract_urls_from_message(event.message)
            if not urls:
                return

            chat = await event.get_chat()
            origem = chat_display_name(chat)
            link_msg = message_deeplink(chat, event.message.id)

            logger.info("Mensagem nova com %d URL(s): %s", len(urls), urls)

            for url in urls:
                casa = match_house(url, houses)
                if not casa:
                    logger.info("URL ignorada (casa nao reconhecida): %s", url)
                    continue
                writer.append_link(
                    canal_origem=origem,
                    msg_link=link_msg,
                    conteudo=text,
                    url=url,
                    casa=casa,
                )
        except Exception as e:
            logger.exception("Erro processando mensagem: %s", e)

    logger.info("Listener ativo. Ctrl+C pra parar.")
    await client.run_until_disconnected()


if __name__ == "__main__":
    setup_logging()
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuario.")
