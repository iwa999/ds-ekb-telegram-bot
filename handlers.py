# handlers.py - Исправленная версия для python-telegram-bot 20.7
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from states import BotStates
from bot_logic import process_data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        ["🔧 AI-диагностика", "📋 Заказать услугу"],
        ["📞 Контакты", "❓ FAQ"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔧 Добро пожаловать в ДС-ЕКБ!\n\n"
        "Мы предоставляем услуги по:\n"
        "• Обслуживанию и чистке вентиляции\n"
        "• Ремонту кондиционеров и сплит-систем\n"
        "• Ремонту промышленного холодильного оборудования\n\n"
        "Выберите нужную опцию:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "ℹ️ Справка по боту ДС-ЕКБ:\n\n"
        "🔧 AI-диагностика - умная диагностика оборудования\n"
        "📋 Заказать услугу - оформить заявку на обслуживание\n"
        "📞 Контакты - наши контактные данные\n"
        "❓ FAQ - часто задаваемые вопросы\n\n"
        "Для отмены операции используйте /cancel"
    )

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Контакты"""
    await update.message.reply_text(
        "📞 Контакты ДС-ЕКБ:\n\n"
        "📱 Телефон: +7 922 130-83-65\n"
        "🌐 Сайт: ds-ekb.ru\n"
        "📧 Email: info@ds-ekb.ru\n"
        "📍 Екатеринбург\n\n"
        "🕒 Режим работы: Пн-Пт 9:00-18:00\n"
        "⚡ Экстренные вызовы: 24/7"
    )

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки FAQ"""
    await update.message.reply_text(
        "❓ Часто задаваемые вопросы:\n\n"
        "Q: Как часто нужно чистить вентиляцию?\n"
        "A: Рекомендуем 1-2 раза в год\n\n"
        "Q: Сколько стоит диагностика кондиционера?\n"
        "A: AI-диагностика БЕСПЛАТНО!\n\n"
        "Q: Работаете ли с промышленным оборудованием?\n"
        "A: Да, это одна из наших специализаций\n\n"
        "Q: Есть ли гарантия на работы?\n"
        "A: Да, гарантия до 2 лет"
    )

async def ai_diagnostics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик AI-диагностики"""
    await update.message.reply_text(
        "🤖 Запуск AI-диагностики оборудования!\n\n"
        "Для точной диагностики мне понадобится несколько данных.\n"
        "Начнем с вашего имени:"
    )
    return BotStates.NAME

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор имени пользователя"""
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        f"Приятно познакомиться, {update.message.text}!\n"
        "Теперь укажите ваш номер телефона:"
    )
    return BotStates.PHONE

async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор телефона пользователя"""
    context.user_data['phone'] = update.message.text
    
    keyboard = [
        ["Вентиляция", "Кондиционер"],
        ["Холодильное оборудование"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📱 Телефон сохранен!\n"
        "Теперь выберите тип оборудования:",
        reply_markup=reply_markup
    )
    return BotStates.EQUIPMENT_TYPE

async def collect_equipment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор типа оборудования"""
    context.user_data['equipment_type'] = update.message.text
    
    keyboard = [["Пропустить"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"✅ Тип оборудования: {update.message.text}\n\n"
        "📸 Пожалуйста, пришлите фото оборудования для более точной диагностики\n"
        "(или нажмите 'Пропустить'):",
        reply_markup=reply_markup
    )
    return BotStates.PHOTO

async def collect_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор фото или завершение диагностики"""
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id
        photo_text = "📸 Фото получено!"
    else:
        context.user_data['photo'] = None
        photo_text = "📸 Фото пропущено"
    
    # Обработка собранных данных
    await process_data(context.user_data, update, context)
    
    await update.message.reply_text(
        f"{photo_text}\n\n"
        "🤖 AI-диагностика завершена!\n"
        "📋 Ваша заявка принята в обработку.\n"
        "📞 Наш специалист свяжется с вами в течение 15 минут!\n\n"
        "Спасибо за обращение в ДС-ЕКБ! 🔧",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Возвращаем в главное меню
    keyboard = [
        ["🔧 AI-диагностика", "📋 Заказать услугу"],
        ["📞 Контакты", "❓ FAQ"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Выберите следующее действие:",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    await update.message.reply_text(
        "❌ Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
