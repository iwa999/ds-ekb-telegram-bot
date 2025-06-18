#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DS EKB Telegram Bot с интеграцией amoCRM
Обновленная версия с новым токеном
"""

import asyncio
import logging
import os
import json
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7437623986:AAFj-sItRC4s889Sop2mglRE7SE2c-drTCY')

# amoCRM Configuration
AMOCRM_SUBDOMAIN = "ekbamodseru"
AMOCRM_API_URL = f"https://{AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/"

# НОВЫЙ ДОЛГОСРОЧНЫЙ ТОКЕН - ОБНОВЛЕН!
AMOCRM_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImI4YWFlMGU1ODA2Nzc1MDAzMjFmMjlhNDYyODI1ZTQ3NjY3MDNkOThjOGE2NDQ1YTNhNTg1M2Y5NDg3YWJjMzU4MGIyNDhmMTAzZjdkZmFmIn0.eyJhdWQiOiJjNDhlMWUwOS04NTVhLTQ3YzItOGQ3Yy0yY2EzM2UxNjhiMWMiLCJqdGkiOiJiOGFhZTBlNTgwNjc3NTAwMzIxZjI5YTQ2MjgyNWU0NzY2NzAzZDk4YzhhNjQ0NWEzYTU4NTNmOTQ4N2FiYzM1ODBiMjQ4ZjEwM2Y3ZGZhZiIsImlhdCI6MTc1MDI2MzQyNSwibmJmIjoxNzUwMjYzNDI1LCJleHAiOjE4NDIzMDcyMDAsInN1YiI6IjEyNjQwMzA2IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNDk0NTU4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiMDBiZDI4ZTMtYTllZS00ZmFiLWI5N2MtYjk0OTdiMDY2MzY4IiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.HvgSDyxs_Lw0opRU7XW95zv1L65Mz-F0XAXdUl_Xwddx6pqP2OXUPXAK-Gr-k85-8nZUV0rtp9fkXHpVh6GpJrKgrnhNCWkv5YHBx29TJj8G-mQEomfrHFv-uzMQt6DY4cktWPAytRqXdloYbv4c_hkMElbqt5M8-fY3GAJY3xLrqzpDtclUh-Hcfyun6-st23-hHdJDWAWCrZxLYK7LcHICZ9XG8EXrx-rNVW_OSRponiYacNAVDW30n-F5hgOdnhrfxAKa-ies35ZakaAHLWtezFl-DP4d0mIQWEVJfeuBAA2LsQng-ct1jbzCnhEGISR4RVviTLufiQrBR9Qp2Q"

async def create_amocrm_contact(name: str, phone: str = None, telegram_id: str = None):
    """Создание контакта в amoCRM"""
    try:
        headers = {
            'Authorization': f'Bearer {AMOCRM_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        contact_data = {
            "name": name,
            "custom_fields_values": []
        }
        
        if phone:
            contact_data["custom_fields_values"].append({
                "field_id": 269005,  # ID поля телефона
                "values": [{"value": phone}]
            })
            
        if telegram_id:
            contact_data["custom_fields_values"].append({
                "field_id": 269007,  # ID поля Telegram
                "values": [{"value": f"@{telegram_id}"}]
            })
        
        response = requests.post(
            f"{AMOCRM_API_URL}contacts",
            headers=headers,
            json=[contact_data]
        )
        
        logger.info(f"Contact creation response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('_embedded', {}).get('contacts'):
                contact_id = result['_embedded']['contacts'][0]['id']
                logger.info(f"✅ Контакт создан: ID {contact_id}")
                return contact_id
        else:
            logger.error(f"❌ Ошибка создания контакта: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании контакта: {e}")
    
    return None

async def create_amocrm_lead(contact_id: int, message_text: str, user_data: dict):
    """Создание сделки в amoCRM"""
    try:
        headers = {
            'Authorization': f'Bearer {AMOCRM_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Определяем тип услуги по тексту
        service_type = "Общая заявка"
        if any(word in message_text.lower() for word in ['вентиляция', 'воздух', 'дым']):
            service_type = "Вентиляция"
        elif any(word in message_text.lower() for word in ['кондиционер', 'сплит', 'охлаждение']):
            service_type = "Кондиционер"
        elif any(word in message_text.lower() for word in ['холодильник', 'морозильник', 'фреон']):
            service_type = "Холодильное оборудование"
        
        lead_data = {
            "name": f"HVAC заявка - {service_type}",
            "price": 5000,  # Предварительная стоимость
            "contacts_to_bind": [contact_id],
            "custom_fields_values": [
                {
                    "field_id": 123456,  # ID поля типа услуги
                    "values": [{"value": service_type}]
                },
                {
                    "field_id": 123457,  # ID поля с описанием
                    "values": [{"value": message_text[:500]}]
                }
            ]
        }
        
        response = requests.post(
            f"{AMOCRM_API_URL}leads",
            headers=headers,
            json=[lead_data]
        )
        
        logger.info(f"Lead creation response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('_embedded', {}).get('leads'):
                lead_id = result['_embedded']['leads'][0]['id']
                logger.info(f"✅ Сделка создана: ID {lead_id}")
                return lead_id
        else:
            logger.error(f"❌ Ошибка создания сделки: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании сделки: {e}")
    
    return None

async def create_amocrm_task(lead_id: int, contact_name: str):
    """Создание задачи в amoCRM"""
    try:
        headers = {
            'Authorization': f'Bearer {AMOCRM_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        task_data = {
            "text": f"Связаться с клиентом {contact_name} по заявке HVAC",
            "complete_till": int((datetime.now().timestamp() + 3600) * 1000),  # +1 час
            "entity_id": lead_id,
            "entity_type": "leads"
        }
        
        response = requests.post(
            f"{AMOCRM_API_URL}tasks",
            headers=headers,
            json=[task_data]
        )
        
        logger.info(f"Task creation response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('_embedded', {}).get('tasks'):
                task_id = result['_embedded']['tasks'][0]['id']
                logger.info(f"✅ Задача создана: ID {task_id}")
                return task_id
        else:
            logger.error(f"❌ Ошибка создания задачи: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании задачи: {e}")
    
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("🔧 AI-диагностика", callback_data='ai_diagnostics')],
        [InlineKeyboardButton("📋 Заказать услугу", callback_data='order_service')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contacts')],
        [InlineKeyboardButton("❓ FAQ", callback_data='faq')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🔧 *Добро пожаловать в DS EKB!*

Мы предоставляем профессиональные услуги:
• Обслуживание вентиляции
• Ремонт кондиционеров  
• Холодильное оборудование

Выберите нужную опцию или просто опишите вашу проблему.
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔧 AI-диагностика", callback_data='ai_diagnostics')],
        [InlineKeyboardButton("📋 Заказать услугу", callback_data='order_service')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contacts')],
        [InlineKeyboardButton("❓ FAQ", callback_data='faq')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query.data == 'ai_diagnostics':
        text = """
🤖 *AI-диагностика оборудования*

Опишите проблему с вашим оборудованием:
• Какое оборудование?
• Что именно не работает?
• Когда началась проблема?

Наш ИИ проанализирует и предложит решение!
        """
    elif query.data == 'order_service':
        text = """
📋 *Заказ услуги*

Для заказа укажите:
• Тип услуги
• Адрес
• Удобное время
• Контактный телефон

Мы свяжемся с вами в течение часа!
        """
    elif query.data == 'contacts':
        text = """
📞 *Контактная информация*

🏢 ООО "ДС ЕКБ"
📱 Телефон: +7 922 130-83-65
🌐 Сайт: ds-ekb.ru
📍 Екатеринбург

⏰ Режим работы: 
Пн-Пт: 8:00-20:00
Сб-Вс: 9:00-18:00

🚨 Аварийная служба: 24/7
        """
    elif query.data == 'faq':
        text = """
❓ *Часто задаваемые вопросы*

🔸 Как быстро приедете?
   Стандартный выезд - в течение 4 часов
   Срочный вызов - в течение 1 часа

🔸 Какова стоимость диагностики?
   Бесплатно при заказе ремонта
   Отдельно - 1000₽

🔸 Даете ли гарантию?
   Да, на все работы - 1 год
   На запчасти - согласно гарантии производителя

🔸 Работаете ли с юридическими лицами?
   Да, работаем с НДС и без НДС
        """
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений (заявок)"""
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"📩 Получена заявка от {user.username}: {message_text}")
    
    # Извлекаем данные пользователя
    name = user.first_name or "Клиент"
    if user.last_name:
        name += f" {user.last_name}"
    
    phone = None
    # Пытаемся найти телефон в сообщении
    import re
    phone_match = re.search(r'(\+7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})', message_text)
    if phone_match:
        phone = phone_match.group(0)
    
    try:
        # Создаем контакт в amoCRM
        contact_id = await create_amocrm_contact(
            name=name,
            phone=phone,
            telegram_id=user.username
        )
        
        if contact_id:
            # Создаем сделку
            lead_id = await create_amocrm_lead(
                contact_id=contact_id,
                message_text=message_text,
                user_data={
                    'telegram_id': user.id,
                    'username': user.username,
                    'name': name
                }
            )
            
            if lead_id:
                # Создаем задачу
                task_id = await create_amocrm_task(lead_id, name)
                
                # Отправляем подтверждение
                success_text = f"""
✅ *Заявка принята!*

📝 Номер заявки: #{lead_id}
👤 Клиент: {name}
📱 Контакт: {phone or 'Telegram: @' + (user.username or str(user.id))}

📋 Ваша заявка:
"{message_text}"

⏰ Мы свяжемся с вами в течение часа!

Благодарим за обращение в DS EKB! 🔧
                """
                
                keyboard = [
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    success_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
                logger.info(f"✅ Заявка обработана: Contact ID {contact_id}, Lead ID {lead_id}")
            else:
                raise Exception("Не удалось создать сделку")
        else:
            raise Exception("Не удалось создать контакт")
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки заявки: {e}")
        
        # Отправляем сообщение об ошибке
        error_text = """
❌ Произошла ошибка при обработке заявки.

Пожалуйста, свяжитесь с нами напрямую:
📞 +7 922 130-83-65

Приносим извинения за неудобства!
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data='start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            error_text,
            reply_markup=reply_markup
        )

def main() -> None:
    """Главная функция запуска бота"""
    logger.info("🤖 Запуск DS EKB Telegram Bot...")
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("✅ Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
