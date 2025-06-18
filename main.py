import os
import logging
import asyncio
import aiohttp
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токены из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
AMOCRM_CLIENT_ID = os.getenv('AMOCRM_CLIENT_ID')
AMOCRM_CLIENT_SECRET = os.getenv('AMOCRM_CLIENT_SECRET')

# Глобальная переменная для хранения access_token
access_token = None
amocrm_subdomain = None

async def get_amocrm_token():
    """Получение access_token для amoCRM"""
    global access_token, amocrm_subdomain
    
    if not AMOCRM_CLIENT_ID or not AMOCRM_CLIENT_SECRET:
        logger.error("Не заданы переменные amoCRM")
        return None
    
    # Здесь должен быть ваш поддомен amoCRM
    amocrm_subdomain = "dsekb"  # Замените на ваш поддомен
    
    # Для упрощения используем долгосрочный токен
    # В реальном проекте здесь была бы полная OAuth авторизация
    logger.info("amoCRM токен настроен")
    access_token = "долгосрочный_токен"  # Здесь будет ваш долгосрочный токен
    return access_token

async def create_amocrm_contact(name, phone, telegram_id):
    """Создание контакта в amoCRM"""
    global access_token, amocrm_subdomain
    
    if not access_token:
        await get_amocrm_token()
    
    contact_data = {
        "name": name,
        "custom_fields_values": [
            {
                "field_id": 264911,  # ID поля телефона (стандартное)
                "values": [{"value": phone, "enum_code": "WORK"}]
            }
        ],
        "custom_fields_values": [
            {
                "field_id": 264913,  # ID поля email (стандартное) 
                "values": [{"value": f"telegram_{telegram_id}@dsekb.local"}]
            }
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://{amocrm_subdomain}.amocrm.ru/api/v4/contacts'
            
            async with session.post(url, json=[contact_data], headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Контакт создан: {result}")
                    return result['_embedded']['contacts'][0]['id']
                else:
                    logger.error(f"Ошибка создания контакта: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при создании контакта: {e}")
        return None

async def create_amocrm_lead(contact_id, service_type, description, telegram_username):
    """Создание сделки в amoCRM"""
    global access_token, amocrm_subdomain
    
    lead_data = {
        "name": f"HVAC заявка - {service_type}",
        "price": 5000,  # Базовая цена
        "pipeline_id": 1,  # ID воронки (обычно 1 - основная)
        "status_id": 142,  # ID статуса "Новая заявка"
        "_embedded": {
            "contacts": [{"id": contact_id}]
        },
        "custom_fields_values": [
            {
                "field_id": 123456,  # ID кастомного поля для описания
                "values": [{"value": description}]
            }
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://{amocrm_subdomain}.amocrm.ru/api/v4/leads'
            
            async with session.post(url, json=[lead_data], headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Сделка создана: {result}")
                    return result['_embedded']['leads'][0]['id']
                else:
                    logger.error(f"Ошибка создания сделки: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при создании сделки: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в DS EKB!\n\n"
        "Мы предоставляем услуги по обслуживанию:\n"
        "🌪️ Вентиляции\n"
        "❄️ Кондиционеров\n"
        "🧊 Холодильного оборудования\n\n"
        "Выберите нужную опцию:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    user = update.effective_user
    
    if text == "🔧 AI-диагностика":
        await update.message.reply_text(
            "🤖 AI-диагностика оборудования\n\n"
            "Опишите проблему в одном сообщении:\n"
            "• Тип оборудования\n"
            "• Симптомы неисправности\n"
            "• Ваши контакты (имя, телефон)\n"
            "• Адрес объекта\n\n"
            "Пример: 'Кондиционер не охлаждает, течет вода. Иван Петров, +7-912-345-67-89, ул. Ленина 10'"
        )
        context.user_data['waiting_for'] = 'diagnostics'
        
    elif text == "📋 Заказать услугу":
        await update.message.reply_text(
            "📋 Заказ услуги\n\n"
            "Опишите что нужно сделать:\n"
            "• Тип услуги (ремонт/обслуживание/чистка)\n"
            "• Тип оборудования\n"
            "• Ваши контакты (имя, телефон)\n"
            "• Адрес объекта\n"
            "• Желаемое время\n\n"
            "Пример: 'Чистка вентиляции в офисе. Мария Сидорова, +7-912-555-77-88, ул. Мира 5, завтра утром'"
        )
        context.user_data['waiting_for'] = 'order'
        
    elif text == "📞 Контакты":
        await update.message.reply_text(
            "📞 Наши контакты:\n\n"
            "☎️ Телефон: +7 922 130-83-65\n"
            "🌐 Сайт: ds-ekb.ru\n"
            "📍 Адрес: г. Екатеринбург\n"
            "🕐 Режим работы: 24/7\n\n"
            "📱 Telegram: @ds_ekb_hvac\n"
            "📘 ВКонтакте: vk.ru/ds_ekb"
        )
        
    elif text == "❓ FAQ":
        await update.message.reply_text(
            "❓ Часто задаваемые вопросы:\n\n"
            "🔹 Сколько стоит диагностика?\n"
            "→ AI-диагностика бесплатно!\n\n"
            "🔹 Как быстро приедете?\n"
            "→ В течение 2 часов по городу\n\n"
            "🔹 Работаете ли в выходные?\n"
            "→ Да, работаем 24/7\n\n"
            "🔹 Гарантия на работы?\n"
            "→ До 2 лет на все виды работ"
        )
        
    else:
        # Обработка заявок
        waiting_for = context.user_data.get('waiting_for')
        
        if waiting_for in ['diagnostics', 'order']:
            # Создаем контакт и сделку в amoCRM
            try:
                # Извлекаем данные из сообщения (упрощенно)
                service_type = "AI-диагностика" if waiting_for == 'diagnostics' else "Заказ услуги"
                
                # Создаем контакт
                contact_id = await create_amocrm_contact(
                    name=user.first_name or "Клиент Telegram",
                    phone="Указать в сообщении",
                    telegram_id=user.id
                )
                
                if contact_id:
                    # Создаем сделку
                    lead_id = await create_amocrm_lead(
                        contact_id=contact_id,
                        service_type=service_type,
                        description=text,
                        telegram_username=user.username or str(user.id)
                    )
                    
                    if lead_id:
                        await update.message.reply_text(
                            "✅ Заявка принята!\n\n"
                            f"📋 Номер заявки: #{lead_id}\n"
                            "📞 Наш менеджер свяжется с вами в течение 15 минут\n\n"
                            "Спасибо за обращение! 🙏"
                        )
                    else:
                        await update.message.reply_text(
                            "✅ Заявка принята!\n\n"
                            "📞 Наш менеджер свяжется с вами в течение 15 минут\n\n"
                            "Спасибо за обращение! 🙏"
                        )
                else:
                    await update.message.reply_text(
                        "✅ Заявка принята!\n\n"
                        "📞 Наш менеджер свяжется с вами в течение 15 минут\n\n"
                        "Спасибо за обращение! 🙏"
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка обработки заявки: {e}")
                await update.message.reply_text(
                    "✅ Заявка принята!\n\n"
                    "📞 Наш менеджер свяжется с вами в течение 15 минут\n\n"
                    "Спасибо за обращение! 🙏"
                )
            
            # Сбрасываем состояние
            context.user_data['waiting_for'] = None
            
        else:
            await update.message.reply_text(
                "Используйте кнопки меню для выбора нужной опции 👆"
            )

def main():
    """Главная функция запуска бота"""
    if not TELEGRAM_TOKEN:
        logger.error("Не задан TELEGRAM_TOKEN")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Инициализируем amoCRM токен при запуске
    asyncio.create_task(get_amocrm_token())
    
    # Запускаем бота
    logger.info("Бот запущен")
    application.run_polling()

if __name__ == '__main__':
    main()
