# handlers.py - Command and button handlers
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from states import BotStates
from bot_logic import process_data

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['AI-диагностика', 'Заказать услугу'], ['Контакты', 'FAQ']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Добро пожаловать в DS-EKB Telegram Bot!", reply_markup=reply_markup)

async def handle_ai_diagnosis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Вентиляция', 'Кондиционеры', 'Холодильное']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите тип оборудования:", reply_markup=reply_markup)
    return BotStates.EQUIPMENT_TYPE

async def handle_order_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заказ услуги: Пожалуйста, введите ваше имя:")
    return BotStates.NAME

async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Контакты: Вы можете связаться с нами по телефону +7 123 456 7890.")

async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FAQ: Часто задаваемые вопросы.")

async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Спасибо! Теперь введите ваш телефон:")
    return BotStates.PHONE

async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Выберите тип оборудования для диагностики:", reply_markup=ReplyKeyboardRemove())
    return BotStates.EQUIPMENT_TYPE

async def collect_equipment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['equipment_type'] = update.message.text
    await update.message.reply_text("Пожалуйста, отправьте фото оборудования:")
    return BotStates.PHOTO

async def collect_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    context.user_data['photo'] = photo_file.file_id
    await update.message.reply_text(f"Спасибо, {context.user_data['name']}! Мы свяжемся с вами по номеру {context.user_data['phone']}.")
    # Process data with AI diagnostics
    await process_data(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
