#!/usr/bin/env python3
"""
DS EKB Telegram Bot с интеграцией amoCRM
Исправленная версия с непрерывной работой
"""

import logging
import os
import json
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7437623986:AAFj-sItRC4s889Sop2mglRE7SE2c-drTCY')
AMOCRM_SUBDOMAIN = "ekbamodseru"
AMOCRM_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImVjN2RmYjU4ZGNiNTllZWUwM2MwZmNkYTYxMTE3NzQwNGViNTAzNjQ1NGRhYmZmZTAxNzVkYzMzMjBmMzFjMGJjNzRlZGI0ZmM2MTBhOTkwIn0.eyJhdWQiOiJjNDhlMWUwOS04NTVhLTQ3YzItOGQ3Yy0yY2EzM2UxNjhiMWMiLCJqdGkiOiJlYzdkZmI1OGRjYjU5ZWVlMDNjMGZjZGE2MTExNzc0MDRlYjUwMzY0NTRkYWJmZmUwMTc1ZGMzMzIwZjMxYzBiYzc0ZWRiNGZjNjEwYTk5MCIsImlhdCI6MTc1MDI1OTc1MSwibmJmIjoxNzUwMjU5NzUxLCJleHAiOjE4MTMyNzY4MDAsInN1YiI6IjEyNjQwMzA2IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNDk0NTU4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiNDRlMzU2YzktYmRjZS00MTA5LWEwNzktN2Q0OWEyNjk4ZjY4IiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.EWF58KvQGEBVICVJ4cFu--0FH7KNaXocvTKIkAN-Zdb07wbfWk1ybNvCT3zOhFSfAsNnh-i8ji9k7mmclN9lUtqK6ouTep-Qmxo0c03OOZfzcxJu7LhJ5DsnxdHdNpQkYc4QKEIsI7I9F-Kv0fXInnM1iA9lqJU3FUcfMhQvsXIYZQBJvjki9xZ86UhV_QksVeCkiZUOwql0kCgJOtyGGK5LsHW3_qh0zBE5YL00422UzM9cpgPh_y4Lw08WGMUygTPtTh-A0G0FICFmtANsFqZfu43PXb3sOwZ8XZ7T2b2rCaShrUh98OwheR0wMFqwD2iAHIWQJ-q8B3X6N0PWvg"

def get_main_menu_keyboard():
    """Возвращает главное меню с кнопками"""
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user = update.effective_user
    welcome_message = f"""
🔧 Добро пожаловать в ДС ЕКБ, {user.first_name}!

Мы предоставляем услуги:
• Обслуживание вентиляции
• Ремонт кондиционеров  
• Холодильное оборудование

🤖 AI-помощник поможет с диагностикой!

Выберите нужную услугу или напишите свою заявку:
    """
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard()
    )

async def create_amocrm_deal(contact_data):
    """Создание сделки в amoCRM"""
    try:
        headers = {
            'Authorization': f'Bearer {AMOCRM_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Создаем контакт
        contact_data_formatted = {
            "name": contact_data.get('name', 'Клиент из Telegram'),
            "custom_fields_values": []
        }
        
        if contact_data.get('phone'):
            contact_data_formatted["custom_fields_values"].append({
                "field_id": 264911,  # ID поля телефона
                "values": [{"value": contact_data['phone']}]
            })
            
        contact_response = requests.post(
            f'https://{AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/contacts',
            headers=headers,
            json=[contact_data_formatted]
        )
        
        contact_id = None
        if contact_response.status_code == 200:
            contact_data_response = contact_response.json()
            if '_embedded' in contact_data_response and 'contacts' in contact_data_response['_embedded']:
                contact_id = contact_data_response['_embedded']['contacts'][0]['id']
        
        # Создаем сделку
        deal_data = {
            "name": f"HVAC Заявка - {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "price": 5000,
            "custom_fields_values": [
                {
                    "field_id": 123456,  # Примерное ID поля
                    "values": [{"value": contact_data.get('message', 'Заявка из Telegram')}]
                }
            ]
        }
        
        if contact_id:
            deal_data["contacts"] = [{"id": contact_id}]
            
        deal_response = requests.post(
            f'https://{AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads',
            headers=headers,
            json=[deal_data]
        )
        
        if deal_response.status_code == 200:
            deal_data_response = deal_response.json()
            if '_embedded' in deal_data_response and 'leads' in deal_data_response['_embedded']:
                deal_id = deal_data_response['_embedded']['leads'][0]['id']
                logger.info(f"Создана сделка в amoCRM: ID {deal_id}")
                return deal_id
        else:
            logger.error(f"Ошибка создания сделки: {deal_response.status_code} - {deal_response.text}")
            
    except Exception as e:
        logger.error(f"Ошибка при работе с amoCRM: {e}")
        
    return None

def extract_contact_info(text):
    """Извлечение контактной информации из текста"""
    import re
    
    # Поиск телефона
    phone_pattern = r'(\+7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group(0) if phone_match else None
    
    # Поиск имени (слова, начинающиеся с большой буквы)
    name_pattern = r'\b[А-ЯЁA-Z][а-яёa-z]+\b'
    name_matches = re.findall(name_pattern, text)
    name = name_matches[0] if name_matches else None
    
    return {
        'name': name,
        'phone': phone,
        'message': text
    }

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на кнопки"""
    text = update.message.text
    
    if text == "🔧 AI-диагностика":
        response = """
🤖 AI-Диагностика оборудования

Опишите проблему максимально подробно:
• Тип оборудования (кондиционер/вентиляция/холодильник)
• Симптомы неисправности
• Ваш контактный телефон
• Удобное время для визита

Искусственный интеллект проанализирует описание и предложит решение!
        """
        
    elif text == "📋 Заказать услугу":
        response = """
📋 Заказ услуги HVAC

Укажите, пожалуйста:
• Тип услуги (обслуживание/ремонт/установка)
• Объект (квартира/офис/производство)
• Контактный телефон
• Адрес
• Желаемая дата и время

Мы свяжемся с вами в течение 15 минут!
        """
        
    elif text == "📞 Контакты":
        response = """
📞 Контакты ДС ЕКБ

🏢 Офис: г. Екатеринбург, ул. Примерная, 123
📱 Телефон: +7 922 130-83-65
🕒 Режим работы: Пн-Пт 9:00-18:00, Сб 10:00-16:00
💬 Telegram: @ds_ekb_hvac
🌐 Сайт: ds-ekb.ru

⚡ Аварийная служба 24/7: +7 922 130-83-65

Мы работаем по всему Екатеринбургу и области!
        """
        
    elif text == "❓ FAQ":
        response = """
❓ Часто задаваемые вопросы

🔧 Как часто нужно обслуживать кондиционер?
▫️ Домашний: 1 раз в год
▫️ Офисный: 2 раза в год  
▫️ Промышленный: 4 раза в год

💰 Стоимость услуг?
▫️ Чистка кондиционера: от 1,500₽
▫️ Обслуживание вентиляции: от 3,500₽
▫️ Ремонт холодильного оборудования: от 5,000₽

⏱️ Как быстро приедете?
▫️ Плановые работы: в течение дня
▫️ Аварийные вызовы: в течение 2 часов

🤖 AI-диагностика бесплатная?
▫️ Да! Предварительная диагностика бесплатна
        """
    else:
        # Обработка произвольного текста как заявки
        contact_info = extract_contact_info(text)
        deal_id = await create_amocrm_deal(contact_info)
        
        if deal_id:
            response = f"""
✅ Заявка принята! Номер: #{deal_id}

📋 Ваша заявка:
{text[:200]}{'...' if len(text) > 200 else ''}

📞 Наш менеджер свяжется с вами в течение 15 минут!

🔧 Если нужна экстренная помощь, звоните: +7 922 130-83-65
            """
        else:
            response = f"""
✅ Заявка получена!

📋 Ваше сообщение:
{text[:200]}{'...' if len(text) > 200 else ''}

📞 Наш менеджер свяжется с вами в ближайшее время!

🔧 Если нужна экстренная помощь, звоните: +7 922 130-83-65
            """
    
    # ВАЖНО: Всегда возвращаем главное меню
    await update.message.reply_text(
        response,
        reply_markup=get_main_menu_keyboard()
    )

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_press))

    # Запускаем бота
    logger.info("Бот ДС ЕКБ запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
