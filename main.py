#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
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

# Настройки amoCRM
AMOCRM_SUBDOMAIN = "ekbamodseru"
AMOCRM_BASE_URL = f"https://{AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4"
AMOCRM_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImVjN2RmYjU4ZGNiNTllZWUwM2MwZmNkYTYxMTE3NzQwNGViNTAzNjQ1NGRhYmZmZTAxNzVkYzMzMjBmMzFjMGJjNzRlZGI0ZmM2MTBhOTkwIn0.eyJhdWQiOiJjNDhlMWUwOS04NTVhLTQ3YzItOGQ3Yy0yY2EzM2UxNjhiMWMiLCJqdGkiOiJlYzdkZmI1OGRjYjU5ZWVlMDNjMGZjZGE2MTExNzc0MDRlYjUwMzY0NTRkYWJmZmUwMTc1ZGMzMzIwZjMxYzBiYzc0ZWRiNGZjNjEwYTk5MCIsImlhdCI6MTc1MDI1OTc1MSwibmJmIjoxNzUwMjU5NzUxLCJleHAiOjE4MTMyNzY4MDAsInN1YiI6IjEyNjQwMzA2IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNDk0NTU4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiNDRlMzU2YzktYmRjZS00MTA5LWEwNzktN2Q0OWEyNjk4ZjY4IiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.EWF58KvQGEBVICVJ4cFu--0FH7KNaXocvTKIkAN-Zdb07wbfWk1ybNvCT3zOhFSfAsNnh-i8ji9k7mmclN9lUtqK6ouTep-Qmxo0c03OOZfzcxJu7LhJ5DsnxdHdNpQkYc4QKEIsI7I9F-Kv0fXInnM1iA9lqJU3FUcfMhQvsXIYZQBJvjki9xZ86UhV_QksVeCkiZUOwql0kCgJOtyGGK5LsHW3_qh0zBE5YL00422UzM9cpgPh_y4Lw08WGMUygTPtTh-A0G0FICFmtANsFqZfu43PXb3sOwZ8XZ7T2b2rCaShrUh98OwheR0wMFqwD2iAHIWQJ-q8B3X6N0PWvg"

# Заголовки для запросов к amoCRM
HEADERS = {
    'Authorization': f'Bearer {AMOCRM_TOKEN}',
    'Content-Type': 'application/json'
}

def create_amocrm_contact(user_data):
    """Создание контакта в amoCRM"""
    try:
        contact_data = {
            "name": user_data.get('name', 'Клиент из Telegram'),
            "custom_fields_values": [
                {
                    "field_code": "PHONE",
                    "values": [{"value": user_data.get('phone', 'Не указан')}]
                },
                {
                    "field_code": "EMAIL", 
                    "values": [{"value": f"telegram_{user_data.get('user_id', 'unknown')}@telegram.local"}]
                }
            ]
        }
        
        response = requests.post(
            f"{AMOCRM_BASE_URL}/contacts",
            headers=HEADERS,
            json=[contact_data]
        )
        
        if response.status_code == 200:
            contact_id = response.json()['_embedded']['contacts'][0]['id']
            logger.info(f"Контакт создан: {contact_id}")
            return contact_id
        else:
            logger.error(f"Ошибка создания контакта: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при создании контакта: {e}")
        return None

def create_amocrm_deal(user_data, contact_id=None):
    """Создание сделки в amoCRM"""
    try:
        deal_name = f"Заявка от {user_data.get('name', 'Telegram пользователь')} - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        deal_data = {
            "name": deal_name,
            "price": 5000,  # Базовая стоимость
            "pipeline_id": 1,  # ID воронки (обычно 1 для основной)
            "status_id": 1,    # ID этапа "Новая заявка"
        }
        
        # Добавляем контакт к сделке если он есть
        if contact_id:
            deal_data["_embedded"] = {
                "contacts": [{"id": contact_id}]
            }
        
        response = requests.post(
            f"{AMOCRM_BASE_URL}/leads",
            headers=HEADERS,
            json=[deal_data]
        )
        
        if response.status_code == 200:
            deal_id = response.json()['_embedded']['leads'][0]['id']
            logger.info(f"Сделка создана: {deal_id}")
            return deal_id
        else:
            logger.error(f"Ошибка создания сделки: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при создании сделки: {e}")
        return None

def create_amocrm_task(deal_id, user_data):
    """Создание задачи в amoCRM"""
    try:
        task_text = f"Обработать заявку из Telegram:\n\n"
        task_text += f"Клиент: {user_data.get('name', 'Не указано')}\n"
        task_text += f"Username: @{user_data.get('username', 'Не указан')}\n"
        task_text += f"Сообщение: {user_data.get('message', 'Не указано')}\n"
        task_text += f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        task_data = {
            "text": task_text,
            "complete_till": int((datetime.now().timestamp() + 86400)),  # +24 часа
            "entity_id": deal_id,
            "entity_type": "leads"
        }
        
        response = requests.post(
            f"{AMOCRM_BASE_URL}/tasks",
            headers=HEADERS,
            json=[task_data]
        )
        
        if response.status_code == 200:
            task_id = response.json()['_embedded']['tasks'][0]['id']
            logger.info(f"Задача создана: {task_id}")
            return task_id
        else:
            logger.error(f"Ошибка создания задачи: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = """🏢 Добро пожаловать в DS EKB!

Мы специализируемся на:
• Обслуживании вентиляции 
• Ремонте кондиционеров
• Холодильном оборудовании

🤖 Просто напишите ваш вопрос или опишите проблему - я создам заявку автоматически!

Или выберите действие из меню:"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    message_text = update.message.text
    
    if message_text == "🔧 AI-диагностика":
        await update.message.reply_text(
            "🔧 AI-диагностика оборудования\n\n"
            "Опишите проблему с вашим оборудованием:\n"
            "• Что не работает?\n"
            "• Какие симптомы?\n"
            "• Когда началась проблема?\n\n"
            "Я создам заявку и наш специалист свяжется с вами!"
        )
    
    elif message_text == "📋 Заказать услугу":
        await update.message.reply_text(
            "📋 Заказ услуги\n\n"
            "Напишите что вам нужно:\n"
            "• Тип услуги\n"
            "• Адрес объекта\n"
            "• Желаемое время\n"
            "• Ваши контакты\n\n"
            "Я оформлю заявку автоматически!"
        )
    
    elif message_text == "📞 Контакты":
        await update.message.reply_text(
            "📞 Наши контакты:\n\n"
            "☎️ Телефон: +7 922 130-83-65\n"
            "📧 Email: info@ds-ekb.ru\n"
            "🌐 Сайт: ds-ekb.ru\n"
            "📍 Екатеринбург\n\n"
            "⏰ Режим работы: 24/7"
        )
    
    elif message_text == "❓ FAQ":
        await update.message.reply_text(
            "❓ Часто задаваемые вопросы:\n\n"
            "🔧 Как часто нужно чистить вентиляцию?\n"
            "Рекомендуем 1-2 раза в год\n\n"
            "❄️ Когда заправлять кондиционер?\n"
            "При снижении холодопроизводительности\n\n"
            "🏢 Работаете с промышленными объектами?\n"
            "Да, обслуживаем любые объекты\n\n"
            "💰 Сколько стоят услуги?\n"
            "От 1500₽, точная цена после диагностики"
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик любого текстового сообщения как заявки"""
    user = update.effective_user
    message_text = update.message.text
    
    # Извлекаем данные пользователя
    user_data = {
        'user_id': user.id,
        'name': user.full_name or f"Пользователь {user.id}",
        'username': user.username or "не указан",
        'message': message_text,
        'phone': "Будет запрошен при обработке заявки"
    }
    
    # Отправляем сообщение о принятии заявки
    await update.message.reply_text(
        "✅ Ваша заявка принята!\n\n"
        f"📝 Текст заявки: {message_text}\n\n"
        "🔄 Создаю сделку в системе..."
    )
    
    try:
        # Создаем контакт в amoCRM
        contact_id = create_amocrm_contact(user_data)
        
        # Создаем сделку в amoCRM
        deal_id = create_amocrm_deal(user_data, contact_id)
        
        if deal_id:
            # Создаем задачу для команды
            task_id = create_amocrm_task(deal_id, user_data)
            
            success_message = (
                "🎉 Заявка успешно создана!\n\n"
                f"📋 Номер сделки: {deal_id}\n"
                "📞 Наш менеджер свяжется с вами в течение 15 минут\n\n"
                "Спасибо за обращение! 🤝"
            )
        else:
            success_message = (
                "⚠️ Заявка принята, но возникла техническая проблема.\n"
                "Наш менеджер обработает её вручную.\n\n"
                "📞 Телефон: +7 922 130-83-65"
            )
        
        await update.message.reply_text(success_message)
        
    except Exception as e:
        logger.error(f"Ошибка обработки заявки: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при создании заявки.\n"
            "Пожалуйста, позвоните нам напрямую:\n"
            "📞 +7 922 130-83-65"
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция"""
    # Получаем токен бота из переменных окружения
    token = os.environ.get('TELEGRAM_TOKEN')
    if not token:
        logger.error("TELEGRAM_TOKEN не найден в переменных окружения")
        return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик кнопок меню
    application.add_handler(MessageHandler(
        filters.Regex("^(🔧 AI-диагностика|📋 Заказать услугу|📞 Контакты|❓ FAQ)$"), 
        handle_buttons
    ))
    
    # ВАЖНО: Обработчик ЛЮБОГО текстового сообщения как заявки
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex("^(🔧 AI-диагностика|📋 Заказать услугу|📞 Контакты|❓ FAQ)$"), 
        handle_text_message
    ))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запускается...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
