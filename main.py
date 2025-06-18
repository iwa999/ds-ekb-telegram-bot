# main.py - Исправленная версия для python-telegram-bot 20.7
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv('TELEGRAM_TOKEN', '7437623986:AAFj-sItRC4s889Sop2mglRE7SE2c-drTCY')

# Основное меню
def get_main_menu():
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение с меню"""
    welcome_text = """
🏢 Добро пожаловать в DS EKB!

Мы специализируемся на:
• Обслуживании вентиляции
• Ремонте кондиционеров  
• Обслуживании холодильного оборудования

Выберите нужную услугу из меню ⬇️
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=get_main_menu()
    )

# Обработка AI-диагностики
async def ai_diagnostics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка запроса AI-диагностики"""
    response = """
🤖 AI-диагностика оборудования

Для точной диагностики опишите проблему:
• Тип оборудования (вентиляция/кондиционер/холодильное)
• Симптомы неисправности
• Когда появилась проблема

Наш ИИ проанализирует данные и предложит решение!

📞 Для срочной консультации: +7 922 130-83-65
    """
    
    await update.message.reply_text(response, parse_mode='HTML')

# Обработка заказа услуги
async def order_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка заказа услуги"""
    response = """
📋 Заказ услуги DS EKB

Наши услуги:
1️⃣ Обслуживание вентиляции (от 2000₽)
2️⃣ Ремонт кондиционеров (от 1500₽)
3️⃣ Обслуживание холодильного оборудования (от 3000₽)

Для заказа укажите:
• Тип услуги
• Адрес объекта
• Удобное время

📞 Связаться с менеджером: +7 922 130-83-65
💬 Или продолжите в этом чате
    """
    
    await update.message.reply_text(response, parse_mode='HTML')

# Контакты
async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка контактной информации"""
    contacts_text = """
📞 Контакты DS EKB

Телефон: +7 922 130-83-65
Email: info@ds-ekb.ru
Сайт: ds-ekb.ru

Режим работы:
Пн-Пт: 08:00 - 20:00
Сб-Вс: 09:00 - 18:00

Аварийная служба: 24/7

📍 Обслуживаем: Екатеринбург и область
    """
    
    await update.message.reply_text(contacts_text, parse_mode='HTML')

# FAQ
async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Часто задаваемые вопросы"""
    faq_text = """
❓ Часто задаваемые вопросы

Q: Как часто нужно обслуживать кондиционер?
A: Рекомендуем 2 раза в год - весной и осенью

Q: Сколько стоит диагностика?
A: AI-диагностика - бесплатно, выезд мастера - от 500₽

Q: Работаете ли вы с юридическими лицами?
A: Да, заключаем договоры и предоставляем все документы

Q: Гарантия на работы?
A: 6 месяцев на все виды работ

📞 Остались вопросы? Звоните: +7 922 130-83-65
    """
    
    await update.message.reply_text(faq_text, parse_mode='HTML')

# Обработка всех остальных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    if "диагностика" in text.lower() or "🔧" in text:
        await ai_diagnostics(update, context)
    elif "заказать" in text.lower() or "📋" in text:
        await order_service(update, context)
    elif "контакт" in text.lower() or "📞" in text:
        await contacts(update, context)
    elif "faq" in text.lower() or "❓" in text:
        await faq(update, context)
    else:
        # Универсальный ответ
        response = """
Спасибо за сообщение! 

Для быстрого ответа используйте кнопки меню или команду /start

📞 Прямая связь: +7 922 130-83-65
        """
        await update.message.reply_text(response)

# Обработка ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ошибок"""
    logger.error(f'Update {update} caused error {context.error}')

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Запуск бота DS-EKB...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()