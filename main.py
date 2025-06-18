#!/usr/bin/env python3
"""
DS EKB Telegram Bot с интеграцией amoCRM
Полная версия с обработкой всех сценариев
"""

import os
import logging
import asyncio
import json
import re
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
WAITING_FOR_SERVICE, WAITING_FOR_DETAILS, WAITING_FOR_CONTACT = range(3)

# Конфигурация
class Config:
    """Центральная конфигурация приложения"""
    
    # Telegram Bot Token
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7437623986:AAFj-sItRC4s889Sop2mglRE7SE2c-drTCY')
    
    # amoCRM Configuration - СТРОКА 42 ИСПРАВЛЕНА
    AMOCRM_CLIENT_ID = "c48e1e09-855a-47c2-8d7c-2ca33e168b1c"
    AMOCRM_CLIENT_SECRET = "wgeSGmOD4GVijBNBKOdtI58B7Zuxtw2lrnMbY0M2Asb47rnvrhmLYORIaQeVP4rQ"
    AMOCRM_SUBDOMAIN = "ekbamodseru"
    AMOCRM_LONG_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImI4YWFlMGU1ODA2Nzc1MDAzMjFmMjlhNDYyODI1ZTQ3NjY3MDNkOThjOGE2NDQ1YTNhNTg1M2Y5NDg3YWJjMzU4MGIyNDhmMTAzZjdkZmFmIn0.eyJhdWQiOiJjNDhlMWUwOS04NTVhLTQ3YzItOGQ3Yy0yY2EzM2UxNjhiMWMiLCJqdGkiOiJiOGFhZTBlNTgwNjc3NTAwMzIxZjI5YTQ2MjgyNWU0NzY2NzAzZDk4YzhhNjQ0NWEzYTU4NTNmOTQ4N2FiYzM1ODBiMjQ4ZjEwM2Y3ZGZhZiIsImlhdCI6MTc1MDI2MzQyNSwibmJmIjoxNzUwMjYzNDI1LCJleHAiOjE4NDIzMDcyMDAsInN1YiI6IjEyNjQwMzA2IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNDk0NTU4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiMDBiZDI4ZTMtYTllZS00ZmFiLWI5N2MtYjk0OTdiMDY2MzY4IiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.HvgSDyxs_Lw0opRU7XW95zv1L65Mz-F0XAXdUl_Xwddx6pqP2OXUPXAK-Gr-k85-8nZUV0rtp9fkXHpVh6GpJrKgrnhNCWkv5YHBx29TJj8G-mQEomfrHFv-uzMQt6DY4cktWPAytRqXdloYbv4c_hkMElbqt5M8-fY3GAJY3xLrqzpDtclUh-Hcfyun6-st23-hHdJDWAWCrZxLYK7LcHICZ9XG8EXrx-rNVW_OSRponiYacNAVDW30n-F5hgOdnhrfxAKa-ies35ZakaAHLWtezFl-DP4d0mIQWEVJfeuBAA2LsQng-ct1jbzCnhEGISR4RVviTLufiQrBR9Qp2Q"
    
    # API URLs
    AMOCRM_API_URL = f"https://{AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4"
    
    # Компания
    COMPANY_NAME = "ДС ЕКБ"
    COMPANY_PHONE = "+7 922 130-83-65"
    
    # Услуги
    SERVICES = {
        "ventilation": {
            "name": "🌬️ Вентиляция",
            "description": "Обслуживание, чистка и дезинфекция вентиляционных систем",
            "price_from": 3500
        },
        "conditioning": {
            "name": "❄️ Кондиционирование", 
            "description": "Ремонт и техническое обслуживание кондиционеров",
            "price_from": 1500
        },
        "refrigeration": {
            "name": "🧊 Холодильное оборудование",
            "description": "Ремонт промышленного холодильного оборудования",
            "price_from": 5000
        }
    }

class AmoCRMManager:
    """Менеджер для работы с amoCRM API"""
    
    def __init__(self):
        self.config = Config()
        self.access_token = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DS-EKB-TelegramBot/1.0',
            'Content-Type': 'application/json'
        })
    
    async def get_access_token(self) -> Optional[str]:
        """Получение access token для API"""
        try:
            # Используем долгосрочный токен
            if self.config.AMOCRM_LONG_TOKEN:
                self.access_token = self.config.AMOCRM_LONG_TOKEN
                logger.info("Используется долгосрочный токен amoCRM")
                return self.access_token
            
            # Если нет долгосрочного токена, используем OAuth
            url = f"{self.config.AMOCRM_API_URL}/oauth2/access_token"
            data = {
                "client_id": self.config.AMOCRM_CLIENT_ID,
                "client_secret": self.config.AMOCRM_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": "authorization_code_here",
                "redirect_uri": "https://example.com"
            }
            
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                logger.info("Получен новый access token")
                return self.access_token
            else:
                logger.error(f"Ошибка получения токена: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении токена: {e}")
            return None
    
    async def create_contact(self, user_data: Dict[str, Any]) -> Optional[int]:
        """Создание контакта в amoCRM"""
        try:
            if not self.access_token:
                await self.get_access_token()
            
            url = f"{self.config.AMOCRM_API_URL}/contacts"
            
            # Извлечение данных из пользовательского сообщения
            contact_data = self._extract_contact_info(user_data)
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = [
                {
                    "name": contact_data.get('name', f"Клиент из Telegram"),
                    "custom_fields_values": []
                }
            ]
            
            # Добавляем телефон если есть
            if contact_data.get('phone'):
                payload[0]["custom_fields_values"].append({
                    "field_id": 264911,  # ID поля телефона
                    "values": [{"value": contact_data['phone'], "enum_code": "WORK"}]
                })
            
            # Добавляем Telegram username
            if user_data.get('telegram_username'):
                payload[0]["custom_fields_values"].append({
                    "field_id": 264913,  # ID поля для Telegram
                    "values": [{"value": f"@{user_data['telegram_username']}"}]
                })
            
            response = self.session.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                contact_id = result['_embedded']['contacts'][0]['id']
                logger.info(f"Создан контакт ID: {contact_id}")
                return contact_id
            else:
                logger.error(f"Ошибка создания контакта: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при создании контакта: {e}")
            return None
    
    async def create_deal(self, user_data: Dict[str, Any], contact_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Создание сделки в amoCRM"""
        try:
            if not self.access_token:
                await self.get_access_token()
            
            # Если нет контакта, создаем его
            if not contact_id:
                contact_id = await self.create_contact(user_data)
            
            url = f"{self.config.AMOCRM_API_URL}/leads"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Определяем услугу и цену
            service_info = self._extract_service_info(user_data.get('message', ''))
            
            deal_name = f"HVAC заявка - {service_info['service_name']}"
            deal_price = service_info['price']
            
            payload = [
                {
                    "name": deal_name,
                    "price": deal_price,
                    "pipeline_id": 7851058,  # ID воронки
                    "status_id": 63505518,   # ID статуса "Новая заявка"
                    "contacts": [{"id": contact_id}] if contact_id else [],
                    "custom_fields_values": [
                        {
                            "field_id": 264915,  # ID поля "Описание заявки"
                            "values": [{"value": user_data.get('message', '')}]
                        },
                        {
                            "field_id": 264917,  # ID поля "Источник"
                            "values": [{"value": "Telegram Bot"}]
                        },
                        {
                            "field_id": 264919,  # ID поля "Тип услуги"
                            "values": [{"value": service_info['service_name']}]
                        }
                    ]
                }
            ]
            
            response = self.session.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                result = response.json()
                deal_data = result['_embedded']['leads'][0]
                deal_id = deal_data['id']
                
                logger.info(f"Создана сделка ID: {deal_id}")
                
                # Создаем задачу для менеджера
                await self.create_task(deal_id, contact_id, user_data)
                
                return {
                    'deal_id': deal_id,
                    'deal_name': deal_name,
                    'price': deal_price,
                    'service': service_info['service_name']
                }
            else:
                logger.error(f"Ошибка создания сделки: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при создании сделки: {e}")
            return None
    
    async def create_task(self, deal_id: int, contact_id: Optional[int], user_data: Dict[str, Any]) -> bool:
        """Создание задачи для менеджера"""
        try:
            url = f"{self.config.AMOCRM_API_URL}/tasks"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Задача на завтра в 10:00
            tomorrow = datetime.now() + timedelta(days=1)
            complete_till = int(tomorrow.replace(hour=10, minute=0).timestamp())
            
            task_text = f"""
🔔 НОВАЯ ЗАЯВКА ИЗ TELEGRAM

👤 Клиент: {user_data.get('first_name', 'Неизвестно')}
📱 Telegram: @{user_data.get('telegram_username', 'не указан')}
📞 Телефон: {self._extract_phone(user_data.get('message', ''))}

📝 Заявка:
{user_data.get('message', '')}

🎯 Действия:
1. Связаться с клиентом в течение 2 часов
2. Уточнить детали заявки
3. Назначить время визита
4. Обновить статус сделки
            """.strip()
            
            payload = [
                {
                    "text": task_text,
                    "complete_till": complete_till,
                    "entity_id": deal_id,
                    "entity_type": "leads",
                    "task_type_id": 1,  # Звонок
                    "responsible_user_id": 12640306  # ID ответственного
                }
            ]
            
            response = self.session.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                logger.info(f"Создана задача для сделки {deal_id}")
                return True
            else:
                logger.error(f"Ошибка создания задачи: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {e}")
            return False
    
    def _extract_contact_info(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Извлечение контактной информации из сообщения"""
        message = user_data.get('message', '')
        
        # Поиск имени
        name_patterns = [
            r'(?:меня зовут|я|имя)[:\s]*([А-Яа-яЁё\s]+)',
            r'([А-Я][а-я]+)[,\s]',
            r'^([А-Я][а-я]+)'
        ]
        
        name = None
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                break
        
        # Поиск телефона
        phone = self._extract_phone(message)
        
        return {
            'name': name or f"{user_data.get('first_name', 'Клиент')} из Telegram",
            'phone': phone
        }
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Извлечение телефона из текста"""
        phone_patterns = [
            r'\+7[- ]?\(?(\d{3})\)?[- ]?(\d{3})[- ]?(\d{2})[- ]?(\d{2})',
            r'8[- ]?\(?(\d{3})\)?[- ]?(\d{3})[- ]?(\d{2})[- ]?(\d{2})',
            r'(\d{3})[- ]?(\d{3})[- ]?(\d{2})[- ]?(\d{2})'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                if pattern.startswith(r'\+7'):
                    return f"+7 {match.group(1)} {match.group(2)}-{match.group(3)}-{match.group(4)}"
                elif pattern.startswith(r'8'):
                    return f"+7 {match.group(1)} {match.group(2)}-{match.group(3)}-{match.group(4)}"
                else:
                    return f"+7 {match.group(1)} {match.group(2)}-{match.group(3)}-{match.group(4)}"
        
        return None
    
    def _extract_service_info(self, message: str) -> Dict[str, Any]:
        """Определение типа услуги из сообщения"""
        message_lower = message.lower()
        
        # Ключевые слова для определения услуги
        service_keywords = {
            "ventilation": ["вентиляц", "воздух", "приток", "вытяжк", "чист", "дезинфекц"],
            "conditioning": ["кондицион", "сплит", "климат", "холод", "тепл", "фреон"],
            "refrigeration": ["холодиль", "морозиль", "камер", "чиллер", "компрессор"]
        }
        
        max_score = 0
        detected_service = "conditioning"  # По умолчанию
        
        for service_key, keywords in service_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > max_score:
                max_score = score
                detected_service = service_key
        
        service_info = Config.SERVICES[detected_service]
        
        return {
            'service_key': detected_service,
            'service_name': service_info['name'],
            'price': service_info['price_from']
        }

class TelegramBotHandlers:
    """Обработчики для Telegram бота"""
    
    def __init__(self):
        self.amocrm = AmoCRMManager()
        self.config = Config()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        
        logger.info(f"Пользователь {user.first_name} ({user.id}) запустил бота")
        
        # Главное меню
        keyboard = [
            [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
            [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")],
            [KeyboardButton("💰 Калькулятор"), KeyboardButton("⭐ Отзывы")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        welcome_text = f"""
🤖 Добро пожаловать в {self.config.COMPANY_NAME}!

Я ваш AI-помощник по обслуживанию климатической техники.

🌟 Что я умею:
• Провести AI-диагностику вашего оборудования
• Принять заявку на обслуживание
• Рассчитать стоимость работ
• Ответить на вопросы

👇 Выберите нужный раздел или просто опишите вашу проблему
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_ai_diagnostics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик AI-диагностики"""
        diagnostics_text = """
🔧 AI-ДИАГНОСТИКА ОБОРУДОВАНИЯ

Опишите проблему максимально подробно:

🌬️ Для вентиляции:
• Слабый приток/вытяжка воздуха
• Посторонние звуки, вибрация
• Неприятные запахи
• Пыль из вентрешеток

❄️ Для кондиционеров:
• Плохо охлаждает/греет
• Течет вода, конденсат
• Странные звуки
• Неприятный запах
• Не включается

🧊 Для холодильного оборудования:
• Не держит температуру
• Постоянно работает компрессор
• Наледь, лед
• Странные звуки

📝 Напишите ваше сообщение, и я проведу AI-анализ!
        """
        
        await update.message.reply_text(diagnostics_text)
    
    async def handle_order_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик заказа услуги"""
        services_text = """
📋 ЗАКАЗ УСЛУГИ

Выберите нужную услугу или опишите проблему:

🌬️ ВЕНТИЛЯЦИЯ (от 3,500₽)
• Чистка и дезинфекция
• Техническое обслуживание  
• Ремонт вентиляционных систем
• AI-мониторинг качества воздуха

❄️ КОНДИЦИОНИРОВАНИЕ (от 1,500₽)
• Ремонт сплит-систем
• Техническое обслуживание
• AI-диагностика неисправностей
• Заправка фреоном

🧊 ХОЛОДИЛЬНОЕ ОБОРУДОВАНИЕ (от 5,000₽)
• Промышленные холодильники
• Морозильные камеры
• AI-контроль температуры
• Чиллеры и льдогенераторы

💬 Напишите:
• Тип оборудования
• Описание проблемы
• Ваши контакты
• Удобное время для визита
        """
        
        await update.message.reply_text(services_text)
    
    async def handle_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик контактов"""
        contacts_text = f"""
📞 КОНТАКТЫ {self.config.COMPANY_NAME}

🏢 Адрес: г. Екатеринбург
📱 Телефон: {self.config.COMPANY_PHONE}
🕐 Режим работы: 24/7

💬 Связь:
• Telegram: @ds_ekb_hvac
• ВКонтакте: vk.com/ds_ekb

⚡ ЭКСТРЕННЫЙ ВЫЗОВ:
Для срочных заявок звоните по телефону
{self.config.COMPANY_PHONE}

🎯 ГАРАНТИИ:
• Выезд мастера в течение 2 часов
• Гарантия на работы до 2 лет
• Фиксированная стоимость после диагностики
        """
        
        keyboard = [
            [KeyboardButton("📞 Позвонить", request_contact=True)],
            [KeyboardButton("🏠 Главное меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(contacts_text, reply_markup=reply_markup)
    
    async def handle_faq(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик FAQ"""
        faq_text = """
❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

🔸 Как быстро приедет мастер?
В течение 2 часов с момента заявки

🔸 Сколько стоит выезд?
Диагностика бесплатно при заказе ремонта

🔸 Какая гарантия на работы?
До 2 лет в зависимости от вида работ

🔸 Работаете ли в выходные?
Да, работаем 24/7 без выходных

🔸 Можно ли оплатить картой?
Да, принимаем наличные и карты

🔸 Что включает ТО кондиционера?
• Чистка фильтров и радиатора
• Проверка давления фреона
• Диагностика электроники
• Обработка антибактериальным составом

🔸 Как часто чистить вентиляцию?
Рекомендуется 1-2 раза в год

💬 Остались вопросы? Пишите или звоните!
        """
        
        await update.message.reply_text(faq_text)
    
    async def handle_calculator(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик калькулятора"""
        calculator_text = """
💰 КАЛЬКУЛЯТОР СТОИМОСТИ

Примерные цены на услуги:

🌬️ ВЕНТИЛЯЦИЯ:
• Чистка бытовой вентиляции: 3,500-5,000₽
• Чистка промышленной: 150-300₽/пог.м
• Дезинфекция системы: +1,500₽
• Замена фильтров: от 800₽

❄️ КОНДИЦИОНЕРЫ:
• ТО сплит-системы: 1,500-2,500₽
• Заправка фреоном: 2,000-3,500₽
• Ремонт электроники: 3,000-8,000₽
• Замена компрессора: 15,000-25,000₽

🧊 ХОЛОДИЛЬНОЕ ОБОРУДОВАНИЕ:
• Диагностика: 2,000₽
• Ремонт термостата: 3,500-5,000₽
• Замена компрессора: 20,000-40,000₽
• ТО промышленной камеры: 8,000-15,000₽

⚡ Точную стоимость определим после диагностики!

📝 Для расчета напишите:
• Тип оборудования
• Описание проблемы
• Площадь помещения
        """
        
        await update.message.reply_text(calculator_text)
    
    async def handle_reviews(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик отзывов"""
        reviews_text = """
⭐ ОТЗЫВЫ НАШИХ КЛИЕНТОВ

⭐⭐⭐⭐⭐ Александр К.
"AI-диагностика реально работает! Нашли проблему за 2 минуты, которую не могли найти полгода. Рекомендую!"

⭐⭐⭐⭐⭐ ООО "СтройИнвест"
"Обслуживаем у них всю технику в офисе. Быстро, качественно, современно. Особенно нравится мобильное приложение."

⭐⭐⭐⭐⭐ Мария П.
"Мастер приехал через час после заявки. Почистил кондиционер, стал работать как новый. Цены адекватные."

⭐⭐⭐⭐⭐ Ресторан "Вкус"
"Ремонтировали промышленный холодильник. Работу выполнили качественно, гарантию дали на 2 года."

📊 СТАТИСТИКА:
• 4.9/5.0 средняя оценка
• 98% довольных клиентов
• 1247+ выполненных заказов

💬 Оставить отзыв можно в наших социальных сетях!
        """
        
        await update.message.reply_text(reviews_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик обычных сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"Получено сообщение от {user.first_name} ({user.id}): {message_text}")
        
        # Проверяем на кнопки меню
        if message_text == "🔧 AI-диагностика":
            await self.handle_ai_diagnostics(update, context)
            return
        elif message_text == "📋 Заказать услугу":
            await self.handle_order_service(update, context)
            return
        elif message_text == "📞 Контакты":
            await self.handle_contacts(update, context)
            return
        elif message_text == "❓ FAQ":
            await self.handle_faq(update, context)
            return
        elif message_text == "💰 Калькулятор":
            await self.handle_calculator(update, context)
            return
        elif message_text == "⭐ Отзывы":
            await self.handle_reviews(update, context)
            return
        elif message_text == "🏠 Главное меню":
            await self.start_command(update, context)
            return
        
        # Обрабатываем как заявку
        await self.process_user_request(update, context)
    
    async def process_user_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка пользовательской заявки"""
        user = update.effective_user
        message_text = update.message.text
        
        # Сначала отвечаем пользователю
        await update.message.reply_text(
            "✅ Заявка принята! Обрабатываю данные...\n\n"
            "🤖 AI анализирует вашу заявку\n"
            "📋 Создаю задачу для мастера\n"
            "📞 Мы свяжемся с вами в течение 2 часов!"
        )
        
        # Подготавливаем данные пользователя
        user_data = {
            'telegram_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'telegram_username': user.username,
            'message': message_text,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Создаем сделку в amoCRM
            deal_result = await self.amocrm.create_deal(user_data)
            
            if deal_result:
                # Успешно создана сделка
                success_message = f"""
🎉 ЗАЯВКА УСПЕШНО СОЗДАНА!

📋 Номер заявки: #{deal_result['deal_id']}
🛠️ Услуга: {deal_result['service']}
💰 Ориентировочная стоимость: от {deal_result['price']:,}₽

⏰ ЧТО ДАЛЬШЕ:
1. Мастер свяжется с вами в течение 2 часов
2. Проведет бесплатную диагностику
3. Рассчитает точную стоимость работ
4. Выполнит ремонт/обслуживание

📞 Экстренная связь: {self.config.COMPANY_PHONE}

Спасибо за обращение в {self.config.COMPANY_NAME}! 🙏
                """
                
                # Главное меню
                keyboard = [
                    [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
                    [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                await update.message.reply_text(success_message, reply_markup=reply_markup)
                
            else:
                # Ошибка создания сделки, но заявка принята
                await update.message.reply_text(
                    "⚠️ Заявка принята, но возникла техническая ошибка при сохранении.\n\n"
                    f"📞 Пожалуйста, продублируйте заявку по телефону {self.config.COMPANY_PHONE}\n\n"
                    "Или попробуйте отправить заявку еще раз через несколько минут."
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке заявки: {e}")
            await update.message.reply_text(
                "❌ Произошла техническая ошибка при обработке заявки.\n\n"
                f"📞 Пожалуйста, обратитесь по телефону {self.config.COMPANY_PHONE}\n\n"
                "Мы обязательно поможем вам решить проблему!"
            )
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик контакта пользователя"""
        contact = update.message.contact
        user = update.effective_user
        
        logger.info(f"Получен контакт: {contact.phone_number} от {user.first_name}")
        
        # Сохраняем контакт пользователя для дальнейшего использования
        context.user_data['phone'] = contact.phone_number
        
        await update.message.reply_text(
            f"📞 Контакт сохранен: {contact.phone_number}\n\n"
            "Теперь наши мастера смогут быстрее с вами связаться!\n\n"
            "📝 Опишите вашу проблему или выберите услугу из меню."
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Уведомляем пользователя об ошибке
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Произошла техническая ошибка. Попробуйте еще раз или обратитесь в поддержку."
            )

class DSEKBBot:
    """Основной класс Telegram бота DS EKB"""
    
    def __init__(self):
        self.config = Config()
        self.handlers = TelegramBotHandlers()
        self.application = None
    
    def setup_handlers(self) -> None:
        """Настройка обработчиков команд и сообщений"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        
        # Обработчик контактов
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handlers.handle_contact))
        
        # Обработчик всех текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.handlers.error_handler)
        
        logger.info("Обработчики настроены")
    
    async def startup(self) -> None:
        """Инициализация бота при запуске"""
        logger.info(f"Запуск бота {self.config.COMPANY_NAME}")
        
        # Инициализируем amoCRM менеджер
        await self.handlers.amocrm.get_access_token()
        
        logger.info("Бот готов к работе!")
    
    async def shutdown(self) -> None:
        """Корректное завершение работы бота"""
        logger.info("Завершение работы бота")
    
    def run(self) -> None:
        """Запуск бота"""
        # Создаем приложение
        self.application = Application.builder().token(self.config.TELEGRAM_TOKEN).build()
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        # Добавляем хуки запуска и завершения
        self.application.post_init = self.startup
        self.application.post_shutdown = self.shutdown
        
        # Запускаем бота
        logger.info("Запуск polling...")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

if __name__ == "__main__":
    try:
        # Создаем и запускаем бота
        bot = DSEKBBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("Бот остановлен")
