from telethon import TelegramClient
from telethon.tl.types import Channel, Chat


def build_client(api_id: int, api_hash: str, session_name: str) -> TelegramClient:
    return TelegramClient(session_name, api_id, api_hash)


def message_deeplink(chat, message_id: int) -> str:
    """
    Monta o link permanente da mensagem.
    - Canal/grupo publico (com username): https://t.me/{username}/{msg_id}
    - Canal/grupo privado: https://t.me/c/{internal_id}/{msg_id}
    """
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message_id}"
    chat_id = getattr(chat, "id", None)
    if chat_id is None:
        return ""
    return f"https://t.me/c/{chat_id}/{message_id}"


def chat_display_name(chat) -> str:
    if isinstance(chat, (Channel, Chat)):
        title = getattr(chat, "title", None)
        if title:
            return title
    username = getattr(chat, "username", None)
    if username:
        return f"@{username}"
    return str(getattr(chat, "id", "desconhecido"))
