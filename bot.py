import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ContentType, BufferedInputFile
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Берем токен из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле! Создайте файл .env и добавьте BOT_TOKEN=ваш_токен")

# Ускоренная сессия
session = AiohttpSession(timeout=30)
bot = Bot(
    token=BOT_TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()


# --- УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ FILE_ID ---
def get_file_id_from_message(message: types.Message):
    """Возвращает file_id и тип медиа из сообщения"""
    
    # Фото (берём самое большое)
    if message.photo:
        return {
            'type': 'ФОТО',
            'file_id': message.photo[-1].file_id,
            'file_unique_id': message.photo[-1].file_unique_id,
            'size': message.photo[-1].width,
            'caption': message.caption
        }
    
    # Видео
    elif message.video:
        return {
            'type': 'ВИДЕО',
            'file_id': message.video.file_id,
            'file_unique_id': message.video.file_unique_id,
            'duration': message.video.duration,
            'width': message.video.width,
            'height': message.video.height,
            'caption': message.caption
        }
    
    # Видеокружок
    elif message.video_note:
        return {
            'type': 'ВИДЕОКРУЖОК',
            'file_id': message.video_note.file_id,
            'file_unique_id': message.video_note.file_unique_id,
            'duration': message.video_note.duration,
            'length': message.video_note.length,
            'caption': message.caption
        }
    
    # GIF / Анимация
    elif message.animation:
        return {
            'type': 'GIF/АНИМАЦИЯ',
            'file_id': message.animation.file_id,
            'file_unique_id': message.animation.file_unique_id,
            'duration': message.animation.duration,
            'width': message.animation.width,
            'height': message.animation.height,
            'caption': message.caption
        }
    
    # Стикер
    elif message.sticker:
        return {
            'type': 'СТИКЕР',
            'file_id': message.sticker.file_id,
            'file_unique_id': message.sticker.file_unique_id,
            'emoji': message.sticker.emoji,
            'set_name': message.sticker.set_name,
            'caption': message.caption
        }
    
    # Документ
    elif message.document:
        return {
            'type': 'ДОКУМЕНТ',
            'file_id': message.document.file_id,
            'file_unique_id': message.document.file_unique_id,
            'file_name': message.document.file_name,
            'mime_type': message.document.mime_type,
            'size': message.document.file_size,
            'caption': message.caption
        }
    
    # Аудио
    elif message.audio:
        return {
            'type': 'АУДИО',
            'file_id': message.audio.file_id,
            'file_unique_id': message.audio.file_unique_id,
            'duration': message.audio.duration,
            'title': message.audio.title,
            'performer': message.audio.performer,
            'caption': message.caption
        }
    
    # Голосовое
    elif message.voice:
        return {
            'type': 'ГОЛОСОВОЕ',
            'file_id': message.voice.file_id,
            'file_unique_id': message.voice.file_unique_id,
            'duration': message.voice.duration,
            'caption': message.caption
        }
    
    # Кастомные эмодзи в тексте
    elif message.text and message.entities:
        emojis = []
        for entity in message.entities:
            if entity.type == "custom_emoji":
                emoji_text = message.text[entity.offset:entity.offset + entity.length]
                emojis.append({
                    'emoji': emoji_text,
                    'file_id': entity.custom_emoji_id,
                    'file_unique_id': entity.custom_emoji_file_unique_id
                })
        if emojis:
            return {
                'type': 'КАСТОМНЫЕ ЭМОДЗИ',
                'emojis': emojis,
                'caption': message.caption
            }
    
    # Кастомные эмодзи в подписи
    elif message.caption and message.caption_entities:
        emojis = []
        for entity in message.caption_entities:
            if entity.type == "custom_emoji":
                emoji_text = message.caption[entity.offset:entity.offset + entity.length]
                emojis.append({
                    'emoji': emoji_text,
                    'file_id': entity.custom_emoji_id,
                    'file_unique_id': entity.custom_emoji_file_unique_id
                })
        if emojis:
            return {
                'type': 'КАСТОМНЫЕ ЭМОДЗИ (в подписи)',
                'emojis': emojis,
                'caption': message.caption
            }
    
    return None


# --- ОБРАБОТЧИК ДЛЯ ВСЕХ ТИПОВ МЕДИА ---
@dp.message(F.content_type.in_([
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.VIDEO_NOTE,
    ContentType.ANIMATION,
    ContentType.STICKER,
    ContentType.DOCUMENT,
    ContentType.AUDIO,
    ContentType.VOICE,
]))
async def handle_media(message: types.Message):
    data = get_file_id_from_message(message)
    
    if not data:
        await message.answer("❌ Не удалось определить тип файла")
        return
    
    # Формируем ответ
    response = f"<b>✅ {data['type']}</b>\n\n"
    response += f"<code>{data['file_id']}</code>\n\n"
    response += f"<b>unique_id:</b> <code>{data['file_unique_id']}</code>\n"
    
    # Дополнительная информация
    if data.get('duration'):
        minutes = data['duration'] // 60
        seconds = data['duration'] % 60
        response += f"<b>Длительность:</b> {minutes}:{seconds:02d}\n"
    
    if data.get('width') and data.get('height'):
        response += f"<b>Размер:</b> {data['width']}×{data['height']}\n"
    
    if data.get('file_name'):
        response += f"<b>Имя файла:</b> {data['file_name']}\n"
    
    if data.get('mime_type'):
        response += f"<b>MIME тип:</b> {data['mime_type']}\n"
    
    if data.get('size'):
        size_kb = data['size'] / 1024
        if size_kb > 1024:
            response += f"<b>Размер:</b> {size_kb/1024:.1f} МБ\n"
        else:
            response += f"<b>Размер:</b> {size_kb:.1f} КБ\n"
    
    if data.get('emoji'):
        response += f"<b>Emoji:</b> {data['emoji']}\n"
    
    if data.get('set_name'):
        response += f"<b>Набор стикеров:</b> {data['set_name']}\n"
    
    if data.get('title'):
        response += f"<b>Название:</b> {data['title']}\n"
    
    if data.get('performer'):
        response += f"<b>Исполнитель:</b> {data['performer']}\n"
    
    if data.get('caption'):
        response += f"\n<b>Подпись:</b> {data['caption']}\n"
    
    await message.answer(response, parse_mode="HTML")


# --- ОБРАБОТЧИК ДЛЯ КАСТОМНЫХ ЭМОДЗИ ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    data = get_file_id_from_message(message)
    
    if data and data['type'] == 'КАСТОМНЫЕ ЭМОДЗИ':
        response = f"<b>✅ {data['type']}</b>\n\n"
        
        for emoji_data in data['emojis']:
            response += f"Эмодзи: {emoji_data['emoji']}\n"
            response += f"<code>{emoji_data['file_id']}</code>\n\n"
        
        await message.answer(response, parse_mode="HTML")
    
    elif message.entities:
        # Проверяем, есть ли кастомные эмодзи в подписи
        data = get_file_id_from_message(message)
        if data:
            await handle_media(message)


# --- ОБРАБОТЧИК ДЛЯ ПЕРЕСЫЛАЕМЫХ СООБЩЕНИЙ ---
@dp.message(F.forward_date)
async def handle_forwarded(message: types.Message):
    data = get_file_id_from_message(message)
    
    if data:
        response = f"<b>✅ {data['type']} (пересланное)</b>\n\n"
        response += f"<code>{data['file_id']}</code>\n\n"
        response += f"<b>unique_id:</b> <code>{data['file_unique_id']}</code>\n"
        
        if data.get('duration'):
            minutes = data['duration'] // 60
            seconds = data['duration'] % 60
            response += f"<b>Длительность:</b> {minutes}:{seconds:02d}\n"
        
        await message.answer(response, parse_mode="HTML")


# --- КОМАНДА /start ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "<b>🎯 Получение FILE_ID любых медиа</b>\n\n"
        "Просто отправь мне любой файл или перешли его:\n\n"
        "📸 <b>Фото</b>\n"
        "🎬 <b>Видео</b>\n"
        "🔄 <b>Видеокружок</b>\n"
        "🎞️ <b>GIF/Анимация</b>\n"
        "🏷️ <b>Стикер</b>\n"
        "📄 <b>Документ</b>\n"
        "🎵 <b>Аудио/Голосовое</b>\n"
        "✨ <b>Кастомные эмодзи</b>\n\n"
        "<i>Я покажу тебе FILE_ID и дополнительную информацию!</i>",
        parse_mode="HTML"
    )


# --- ЗАПУСК БОТА ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("\n" + "="*50)
    print("🎯 БОТ ДЛЯ ПОЛУЧЕНИЯ FILE_ID")
    print("="*50)
    print("📤 Отправь любой файл или перешли его")
    print("📋 Бот покажет FILE_ID и информацию")
    print("="*50 + "\n")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Бот остановлен")