from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from amocrm_integration import amocrm
import logging

# Состояния диалога
COLLECT_NAME, COLLECT_PHONE, COLLECT_DESCRIPTION = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🏢 Добро пожаловать в ДС ЕКБ!\n\n"
        "Мы предоставляем услуги по:\n"
        "• Обслуживанию вентиляции\n"
        "• Ремонту кондиционеров\n"
        "• Холодильному оборудованию\n\n"
        "Выберите интересующую услугу:",
        reply_markup=reply_markup
    )

async def ai_diagnostics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик AI-диагностики"""
    context.user_data['service_type'] = 'AI-диагностика'
    
    await update.message.reply_text(
        "🤖 AI-диагностика оборудования\n\n"
        "Для точной диагностики мне нужны ваши данные.\n"
        "Как к вам обращаться?"
    )
    return COLLECT_NAME

async def order_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик заказа услуги"""
    context.user_data['service_type'] = 'Заказ услуги'
    
    await update.message.reply_text(
        "📋 Заказ услуги\n\n"
        "Отлично! Оформим заявку на обслуживание.\n"
        "Как к вам обращаться?"
    )
    return COLLECT_NAME

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор имени пользователя"""
    name = update.message.text
    context.user_data['name'] = name
    
    await update.message.reply_text(
        f"Приятно познакомиться, {name}!\n\n"
        "Теперь укажите ваш номер телефона для связи:"
    )
    return COLLECT_PHONE

async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор телефона пользователя"""
    phone = update.message.text
    context.user_data['phone'] = phone
    
    await update.message.reply_text(
        "📝 Опишите проблему с оборудованием или укажите "
        "какая услуга вам нужна (тип оборудования, симптомы и т.д.):"
    )
    return COLLECT_DESCRIPTION

async def collect_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор описания проблемы и отправка в amoCRM"""
    description = update.message.text
    
    # Подготавливаем данные для amoCRM
    user_data = {
        'name': context.user_data.get('name'),
        'phone': context.user_data.get('phone'),
        'telegram_id': update.effective_user.username or str(update.effective_user.id),
        'service_type': context.user_data.get('service_type'),
        'description': description
    }
    
    await update.message.reply_text("⏳ Обрабатываю заявку...")
    
    # Отправляем в amoCRM
    success = amocrm.process_telegram_request(user_data)
    
    if success:
        await update.message.reply_text(
            "✅ Заявка успешно принята!\n\n"
            "📋 Ваша заявка автоматически создана в нашей CRM-системе\n"
            "📞 Менеджер свяжется с вами в ближайшее время\n"
            "📱 Следить за статусом можно в нашем канале: @ds_ekb_hvac\n\n"
            "Спасибо за обращение в ДС ЕКБ!"
        )
        
        # Логируем успешную заявку
        logging.info(f"Заявка создана: {user_data}")
        
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при создании заявки.\n\n"
            "Попробуйте еще раз или свяжитесь с нами напрямую:\n"
            "📞 +7 922 130-83-65"
        )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    return ConversationHandler.END

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик контактов"""
    await update.message.reply_text(
        "📞 Наши контакты:\n\n"
        "🏢 ДС ЕКБ - HVAC услуги\n"
        "📱 Телефон: +7 922 130-83-65\n"
        "🌐 Сайт: ds-ekb.ru\n"
        "📧 Telegram: @dsekb_assistant_bot\n"
        "📍 г. Екатеринбург\n\n"
        "🕒 Работаем 24/7\n"
        "⚡ Экстренный выезд в течение 2 часов"
    )

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик FAQ"""
    await update.message.reply_text(
        "❓ Часто задаваемые вопросы:\n\n"
        "🔧 Какие услуги вы предоставляете?\n"
        "• Чистка и обслуживание вентиляции\n"
        "• Ремонт кондиционеров и сплит-систем\n"
        "• Обслуживание холодильного оборудования\n\n"
        "💰 Сколько стоят услуги?\n"
        "• Диагностика - бесплатно\n"
        "• Чистка вентиляции - от 3500₽\n"
        "• Ремонт кондиционеров - от 1500₽\n\n"
        "⏰ Как быстро приедете?\n"
        "• Плановые работы - в течение дня\n"
        "• Экстренный выезд - в течение 2 часов\n\n"
        "🤖 Что такое AI-диагностика?\n"
        "ИИ анализирует симптомы и определяет неисправность за 2 минуты!"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text("Операция отменена. Напишите /start для начала.")
    context.user_data.clear()
    return ConversationHandler.END
