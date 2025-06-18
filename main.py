# main.py - Исправленная версия для python-telegram-bot 20.7
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler

# Импорт наших модулей
from handlers import start, help_command, contacts, faq, ai_diagnostics, collect_name, collect_phone, collect_equipment_type, collect_photo, cancel
from states import BotStates
from config import TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Обработчик диалога для сбора данных
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔧 AI-диагностика$"), ai_diagnostics)],
        states={
            BotStates.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_name)],
            BotStates.PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_phone)],
            BotStates.EQUIPMENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_equipment_type)],
            BotStates.PHOTO: [MessageHandler(filters.PHOTO, collect_photo), MessageHandler(filters.Regex("^Пропустить$"), collect_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), contacts))
    application.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), faq))
    application.add_handler(conv_handler)
    
    # Запуск бота
    logger.info("Бот ДС-ЕКБ запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()