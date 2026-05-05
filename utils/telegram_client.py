from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat


def build_client(api_id: int, api_hash: str, session_name: str, string_session: str | None = None) -> TelegramClient:
    if string_session:
        return TelegramClient(StringSession(string_session), api_id, api_hash)
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


def describe_media(message) -> str:
    """
    Retorna um marcador tipo [FOTO], [VIDEO] etc se a mensagem tem midia.
    String vazia se for so texto.
    """
    if getattr(message, "photo", None):
        return "[FOTO]"
    if getattr(message, "video", None):
        return "[VIDEO]"
    if getattr(message, "video_note", None):
        return "[VIDEO CIRCULAR]"
    if getattr(message, "voice", None):
        return "[AUDIO]"
    if getattr(message, "audio", None):
        return "[AUDIO]"
    if getattr(message, "gif", None):
        return "[GIF]"
    if getattr(message, "sticker", None):
        return "[STICKER]"
    if getattr(message, "document", None):
        return "[DOCUMENTO]"
    if getattr(message, "poll", None):
        return "[ENQUETE]"
    if getattr(message, "contact", None):
        return "[CONTATO]"
    if getattr(message, "geo", None):
        return "[LOCALIZACAO]"
    return ""


def build_message_content(message) -> str:
    """
    Monta o texto que vai pra coluna 'Conteudo da Mensagem' da planilha.
    Combina tag de midia (se houver) + texto/caption.
    """
    text = (getattr(message, "message", None) or "").strip()
    tag = describe_media(message)
    if tag and text:
        return f"{tag} {text}"
    if tag:
        return tag
    return text or "[MENSAGEM SEM CONTEUDO]"
