#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DS-EKB Telegram Bot с интеграцией amoCRM
Автоматическое создание сделок из заявок в Telegram
"""

import os
import logging
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

# amoCRM настройки с вашими данными
AMOCRM_SUBDOMAIN = "ekbamodseru"
AMOCRM_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImVjN2RmYjU4ZGNiNTllZWUwM2MwZmNkYTYxMTE3NzQwNGViNTAzNjQ1NGRhYmZmZTAxNzVkYzMzMjBmMzFjMGJjNzRlZGI0ZmM2MTBhOTkwIn0.eyJhdWQiOiJjNDhlMWUwOS04NTVhLTQ3YzItOGQ3Yy0yY2EzM2UxNjhiMWMiLCJqdGkiOiJlYzdkZmI1OGRjYjU5ZWVlMDNjMGZjZGE2MTExNzc0MDRlYjUwMzY0NTRkYWJmZmUwMTc1ZGMzMzIwZjMxYzBiYzc0ZWRiNGZjNjEwYTk5MCIsImlhdCI6MTc1MDI1OTc1MSwibmJmIjoxNzUwMjU5NzUxLCJleHAiOjE4MTMyNzY4MDAsInN1YiI6IjEyNjQwMzA2IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNDk0NTU4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiNDRlMzU2YzktYmRjZS00MTA5LWEwNzktN2Q0OWEyNjk4ZjY4IiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.EWF58KvQGEBVICVJ4cFu--0FH7KNaXocvTKIkAN-Zdb07wbfWk1ybNvCT3zOhFSfAsNnh-i8ji9k7mmclN9lUtqK6ouTep-Qmxo0c03OOZfzcxJu7LhJ5DsnxdHdNpQkYc4QKEIsI7I9F-Kv0fXInnM1iA9lqJU3FUcfMhQvsXIYZQBJvjki9xZ86UhV_QksVeCkiZUOwql0kCgJOtyGGK5LsHW3_qh0zBE5YL00422UzM9cpgPh_y4Lw08WGMUygTPtTh-A0G0FICFmtANsFqZfu43PXb3sOwZ8XZ7T2b2rCaShrUh98OwheR0wMFqwD2iAHIWQJ-q8B3X6N0PWvg"

# API endpoints
AMOCRM_API_URL = f"https://{AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4"

class AmoCRMAPI:
    """Класс для работы с amoCRM API"""
    
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {AMOCRM_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def create_contact(self, name, phone, telegram_id):
        """Создание контакта в amoCRM"""
        try:
            url = f"{AMOCRM_API_URL}/contacts"
            
            data = {
                "name": name,
                "custom_fields_values": [
                    {
                        "field_code": "PHONE",
                        "values": [
                            {
                                "value": phone,
                                "enum_code": "WORK"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(url, headers=self.headers, json=[data])
            
            if response.status_code == 200:
                contact_data = response.json()
                contact_id = contact_data['_embedded']['contacts'][0]['id']
                logger.info(f"Контакт создан: {contact_id}")
                return contact_id
            else:
                logger.error(f"Ошибка создания контакта: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при создании контакта: {e}")
            return None
    
    def create_lead(self, name, contact_id, service_type, description=""):
        """Создание сделки в amoCRM"""
        try:
            url = f"{AMOCRM_API_URL}/leads"
            
            # Определяем цену в зависимости от типа услуги
            price_map = {
                "вентиляция": 3500,
                "кондиционер": 1500,
                "холодильное": 5000
            }
            
            price = 0
            for key, value in price_map.items():
                if key in service_type.lower():
                    price = value
                    break
            
            data = {
                "name": f"HVAC заявка: {name}",
                "price": price,
                "contacts": [
                    {
                        "id": contact_id
                    }
                ],
                "custom_fields_values": [
                    {
                        "field_code": "STATUS_ID",
                        "values": [
                            {
                                "value": "Новая заявка"
                            }
                        ]
                    }
                ]
            }
            
            if description:
                data["custom_fields_values"].append({
                    "field_code": "COMMENTS",
                    "values": [
                        {
                            "value": f"Тип услуги: {service_type}\nОписание: {description}\nИсточник: Telegram Bot"
                        }
                    ]
                })
            
            response = requests.post(url, headers=self.headers, json=[data])
            
            if response.status_code == 200:
                lead_data = response.json()
                lead_id = lead_data['_embedded']['leads'][0]['id']
                logger.info(f"Сделка создана: {lead_id}")
                return lead_id
            else:
                logger.error(f"Ошибка создания сделки: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при создании сделки: {e}")
            return None
    
    def create_task(self, lead_id, text="Связаться с клиентом"):
        """Создание задачи в amoCRM"""
        try:
            url = f"{AMOCRM_API_URL}/tasks"
            
            # Задача на завтра в 10:00
            tomorrow = datetime.now().timestamp() + 86400
            
            data = {
                "text": text,
                "complete_till": int(tomorrow),
                "entity_id": lead_id,
                "entity_type": "leads"
            }
            
            response = requests.post(url, headers=self.headers, json=[data])
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data['_embedded']['tasks'][0]['id']
                logger.info(f"Задача создана: {task_id}")
                return task_id
            else:
                logger.error(f"Ошибка создания задачи: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {e}")
            return None

# Инициализация amoCRM API
amocrm = AmoCRMAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = """
🏢 Добро пожаловать в DS EKB!

Мы специализируемся на:
• Обслуживании вентиляции
• Ремонте кондиционеров  
• Холодильном оборудовании

🤖 Выберите нужную опцию в меню ниже
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    text = update.message.text
    
    if text == "🔧 AI-диагностика":
        await update.message.reply_text(
            "🔍 AI-диагностика оборудования\n\n"
            "Опишите проблему в одном сообщении:\n"
            "• Ваше имя\n"
            "• Телефон для связи\n" 
            "• Тип оборудования (вентиляция/кондиционер/холодильное)\n"
            "• Описание проблемы\n\n"
            "Пример:\n"
            "Иван Петров\n"
            "+7 922 123-45-67\n"
            "Кондиционер\n"
            "Не охлаждает, странный звук"
        )
        
    elif text == "📋 Заказать услугу":
        await update.message.reply_text(
            "📋 Заказ услуги\n\n"
            "Укажите в одном сообщении:\n"
            "• Ваше имя\n"
            "• Телефон для связи\n"
            "• Адрес\n" 
            "• Тип услуги\n"
            "• Желаемое время\n\n"
            "Пример:\n"
            "Мария Сидорова\n"
            "+7 922 123-45-67\n"
            "ул. Ленина, 15\n"
            "Чистка вентиляции\n"
            "Завтра после 14:00"
        )
        
    elif text == "📞 Контакты":
        await update.message.reply_text(
            "📞 Наши контакты:\n\n"
            "🏢 ООО «ДС ЕКБ»\n"
            "📱 Телефон: +7 922 130-83-65\n"
            "🌐 Сайт: ds-ekb.ru\n"
            "📍 Екатеринбург\n\n"
            "⏰ Режим работы:\n"
            "Пн-Пт: 9:00-18:00\n"
            "Сб: 10:00-16:00\n"
            "Вс: выходной\n\n"
            "🚨 Аварийные вызовы: 24/7"
        )
        
    elif text == "❓ FAQ":
        await update.message.reply_text(
            "❓ Часто задаваемые вопросы:\n\n"
            "🔧 Какие услуги вы предоставляете?\n"
            "Обслуживание вентиляции, ремонт кондиционеров, холодильное оборудование\n\n"
            "💰 Сколько стоят услуги?\n"
            "Вентиляция: от 3,500₽\n"
            "Кондиционеры: от 1,500₽\n"
            "Холодильное: от 5,000₽\n\n"
            "⏱️ Как быстро приедете?\n"
            "Плановые работы: в течение дня\n"
            "Аварийные: в течение 2 часов\n\n"
            "🛡️ Даете ли гарантию?\n"
            "Да, на все работы 6 месяцев"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    message_text = update.message.text
    user = update.effective_user
    
    # Проверяем, содержит ли сообщение заявку
    lines = message_text.strip().split('\n')
    
    if len(lines) >= 3:  # Минимум имя, телефон, описание
        try:
            # Парсим данные заявки
            name = lines[0].strip()
            phone = lines[1].strip()
            service_type = "Общий запрос"
            description = message_text
            
            # Определяем тип услуги
            text_lower = message_text.lower()
            if any(word in text_lower for word in ['вентиляция', 'вентилятор', 'воздух']):
                service_type = "Вентиляция"
            elif any(word in text_lower for word in ['кондиционер', 'сплит', 'охлаждение']):
                service_type = "Кондиционер"
            elif any(word in text_lower for word in ['холодильник', 'морозильник', 'холодильное']):
                service_type = "Холодильное оборудование"
            
            # Создаем контакт в amoCRM
            contact_id = amocrm.create_contact(name, phone, user.id)
            
            if contact_id:
                # Создаем сделку
                lead_id = amocrm.create_lead(name, contact_id, service_type, description)
                
                if lead_id:
                    # Создаем задачу
                    amocrm.create_task(lead_id, f"Обработать заявку: {service_type}")
                    
                    # Подтверждение пользователю
                    await update.message.reply_text(
                        f"✅ Заявка принята!\n\n"
                        f"📋 Номер заявки: #{lead_id}\n"
                        f"👤 Клиент: {name}\n"
                        f"🔧 Услуга: {service_type}\n"
                        f"📞 Телефон: {phone}\n\n"
                        f"🕐 Наш менеджер свяжется с вами в течение 30 минут!\n\n"
                        f"📱 Для срочных вопросов звоните: +7 922 130-83-65"
                    )
                    
                    logger.info(f"Заявка создана: Lead ID {lead_id}, Contact ID {contact_id}")
                else:
                    await update.message.reply_text(
                        "❌ Ошибка при создании заявки. Позвоните нам: +7 922 130-83-65"
                    )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при обработке данных. Позвоните нам: +7 922 130-83-65"
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки заявки: {e}")
            await update.message.reply_text(
                "❌ Ошибка при обработке заявки. Позвоните нам: +7 922 130-83-65"
            )
    else:
        # Обычное сообщение
        await update.message.reply_text(
            "🤖 Я помогу вам с заказом услуг HVAC!\n\n"
            "Используйте кнопки меню или опишите вашу заявку в формате:\n"
            "• Имя\n"
            "• Телефон\n"
            "• Тип услуги\n"
            "• Описание проблемы"
        )

def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.Regex("^(🔧 AI-диагностика|📋 Заказать услугу|📞 Контакты|❓ FAQ)$"), 
        handle_buttons
    ))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("Бот DS-EKB запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
