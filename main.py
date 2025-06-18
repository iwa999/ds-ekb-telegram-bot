#!/usr/bin/env python3
"""
DS EKB Telegram Bot - Главный файл запуска
Модульная архитектура с amoCRM интеграцией
"""

import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import Config
from handlers import BotHandlers
from utils import setup_logging

async def main():
    """Главная функция запуска бота"""
    
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Создание приложения
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # Инициализация обработчиков
        handlers = BotHandlers()
        
        # Регистрация команд
        application.add_handler(CommandHandler("start", handlers.start_command))
        application.add_handler(CommandHandler("help", handlers.help_command))
        application.add_handler(CommandHandler("status", handlers.status_command))
        
        # Обработчик всех текстовых сообщений
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handlers.handle_message
        ))
        
        # Обработчик фото
        application.add_handler(MessageHandler(
            filters.PHOTO, 
            handlers.handle_photo
        ))
        
        logger.info("🚀 DS EKB Bot запускается...")
        logger.info(f"📋 Модулей загружено: 5")
        logger.info(f"🔗 amoCRM интеграция: включена")
        
        # Запуск бота
        await application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
