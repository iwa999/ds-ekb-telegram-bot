# handlers.py - Исправленная версия для python-telegram-bot 20.7
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from states import BotStates
from bot_logic import process_data

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === КОМАНДА START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем клавиатуру с основными кнопками
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    welcome_text = f"""
🏢 Добро пожаловать в ДС-ЕКБ!

Привет, {user.first_name}! 👋

Мы специализируемся на:
• Обслуживании вентиляции
• Ремонте кондиционеров  
• Промышленном холодильном оборудовании

Выберите нужную услугу из меню ⬇️
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ConversationHandler.END

# === ОБРАБОТЧИК AI-ДИАГНОСТИКИ ===
async def ai_diagnostics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопки AI-диагностика"""
    logger.info(f"AI-диагностика запрошена пользователем {update.effective_user.first_name}")
    
    # Создаем клавиатуру для выбора типа оборудования
    keyboard = [
        [KeyboardButton("❄️ Кондиционер"), KeyboardButton("🌪️ Вентиляция")],
        [KeyboardButton("🧊 Холодильное оборудование")],
        [KeyboardButton("🔙 Назад в меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = """
🤖 AI-диагностика оборудования

Искусственный интеллект поможет определить проблему и рассчитать стоимость ремонта.

Выберите тип оборудования:
    """
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return BotStates.EQUIPMENT_TYPE

# === ОБРАБОТЧИК ЗАКАЗА УСЛУГИ ===
async def order_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопки Заказать услугу"""
    logger.info(f"Заказ услуги запрошен пользователем {update.effective_user.first_name}")
    
    text = """
📋 Заказ услуги

Для оформления заявки нам нужно узнать о вас немного информации.

Как вас зовут?
Напишите ваше имя:
    """
    
    await update.message.reply_text(text, parse_mode='HTML')
    return BotStates.NAME

# === ОБРАБОТЧИК ТИПА ОБОРУДОВАНИЯ ===
async def equipment_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора типа оборудования"""
    equipment_type = update.message.text
    
    if equipment_type == "🔙 Назад в меню":
        return await start(update, context)
    
    # Сохраняем тип оборудования
    context.user_data['equipment_type'] = equipment_type
    
    text = f"""
✅ Выбрано: {equipment_type}

📸 Пришлите фото оборудования
Это поможет AI точнее определить проблему.

Если фото нет, напишите "нет фото"
    """
    
    await update.message.reply_text(text, parse_mode='HTML')
    return BotStates.PHOTO

# === СБОР ИМЕНИ ===
async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбор имени пользователя"""
    name = update.message.text
    context.user_data['name'] = name
    
    text = f"""
👋 Приятно познакомиться, {name}!

📱 Укажите номер телефона
Наш мастер свяжется с вами для уточнения деталей.

Пример: +7 922 123-45-67
    """
    
    await update.message.reply_text(text, parse_mode='HTML')
    return BotStates.PHONE

# === СБОР ТЕЛЕФОНА ===
async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбор номера телефона"""
    phone = update.message.text
    context.user_data['phone'] = phone
    
    # Создаем клавиатуру для выбора типа оборудования
    keyboard = [
        [KeyboardButton("❄️ Кондиционер"), KeyboardButton("🌪️ Вентиляция")],
        [KeyboardButton("🧊 Холодильное оборудование")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = """
📋 Выберите тип оборудования
Какое оборудование требует обслуживания?
    """
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return BotStates.EQUIPMENT_TYPE

# === ОБРАБОТКА ФОТО ===
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка загруженного фото или текста"""
    
    if update.message.photo:
        # Получаем фото
        photo_file = await update.message.photo[-1].get_file()
        context.user_data['photo'] = photo_file.file_path
        logger.info(f"Получено фото от {update.effective_user.first_name}")
        
        response_text = "📸 Фото получено! Анализирую..."
    else:
        # Получаем текст
        text = update.message.text
        context.user_data['photo'] = text
        response_text = "📝 Информация принята! Обрабатываю..."
    
    await update.message.reply_text(response_text)
    
    # Обрабатываем данные
    result = await process_data(context.user_data)
    
    # Возвращаем на главное меню
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    final_text = f"""
✅ Диагностика завершена!

{result}

🎯 Что дальше?
Наш мастер свяжется с вами в ближайшее время для уточнения деталей и согласования времени визита.

Выберите другую услугу или вернитесь в главное меню ⬇️
    """
    
    await update.message.reply_text(
        final_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ConversationHandler.END

# === КОНТАКТЫ ===
async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопки Контакты"""
    text = """
📞 Наши контакты

🏢 ООО "ДС-ЕКБ"
📍 г. Екатеринбург

📱 Телефон: +7 922 130-83-65
⏰ Режим работы: 24/7

💬 Telegram: @ds_ekb_hvac
📧 VK: vk.ru/ds_ekb

Работаем по всему Екатеринбургу и области!
    """
    
    await update.message.reply_text(text, parse_mode='HTML')
    return ConversationHandler.END

# === FAQ ===
async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопки FAQ"""
    text = """
❓ Часто задаваемые вопросы

🕐 Как быстро приедет мастер?
В течение 2-4 часов в рабочее время, экстренный выезд - в течение часа.

💰 Сколько стоит диагностика?
Диагностика БЕСПЛАТНО при заказе ремонта!

🔧 Какие гарантии на работы?
Гарантия на все виды работ от 6 месяцев до 2 лет.

💳 Как можно оплатить?
Наличными, картой, безналичный расчет.

🏠 Выезжаете ли на дом?
Да, работаем по всему Екатеринбургу и области.

📱 Есть ли экстренная служба?
Да, круглосуточно по телефону +7 922 130-83-65
    """
    
    await update.message.reply_text(text, parse_mode='HTML')
    return ConversationHandler.END

# === ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик всех текстовых сообщений"""
    text = update.message.text
    
    # Маршрутизация по тексту кнопок
    if text == "🔧 AI-диагностика":
        return await ai_diagnostics(update, context)
    elif text == "📋 Заказать услугу":
        return await order_service(update, context)
    elif text == "📞 Контакты":
        return await contacts(update, context)
    elif text == "❓ FAQ":
        return await faq(update, context)
    elif text in ["❄️ Кондиционер", "🌪️ Вентиляция", "🧊 Холодильное оборудование"]:
        return await equipment_type_handler(update, context)
    else:
        # Неизвестная команда
        await update.message.reply_text(
            "🤔 Не понимаю эту команду. Используйте кнопки меню ⬇️"
        )
        return ConversationHandler.END

# === ОТМЕНА РАЗГОВОРА ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущего разговора"""
    await update.message.reply_text(
        '❌ Операция отменена. Возвращаюсь в главное меню.',
        reply_markup=ReplyKeyboardRemove()
    )
    
    return await start(update, context)

# === ОБРАБОТКА ОШИБОК ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😵 Произошла ошибка. Попробуйте еще раз или обратитесь в поддержку."
        )
