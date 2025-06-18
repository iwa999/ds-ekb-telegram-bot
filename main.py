# main.py - Entry point for the bot
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from handlers import handle_start, handle_ai_diagnosis, handle_order_service, handle_contacts, handle_faq, collect_name, collect_phone, collect_equipment_type, collect_photo, cancel
from config import TOKEN
from states import BotStates

async def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    # Conversation handler for collecting client data
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(AI-диагностика|Заказать услугу)$'), handle_ai_diagnosis)],
        states={
            BotStates.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_name)],
            BotStates.PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_phone)],
            BotStates.EQUIPMENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_equipment_type)],
            BotStates.PHOTO: [MessageHandler(filters.PHOTO, collect_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("contacts", handle_contacts))
    application.add_handler(CommandHandler("faq", handle_faq))
    application.add_handler(conv_handler)

    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(start_bot())
