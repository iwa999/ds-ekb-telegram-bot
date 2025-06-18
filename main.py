 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DS EKB Telegram Bot с интеграцией amoCRM
Единый файл со всем функционалом
"""

import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

# ===== КОНФИГУРАЦИЯ =====
class Config:
    """Конфигурация бота"""
    
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7437623986:AAFj-sItRC4s889Sop2mglRE7SE2c-drTCY')
    
    # amoCRM
    AMOCRM_SUBDOMAIN = 'ekbamodseru'
    AMOCRM_CLIENT_ID = os.getenv('AMOCRM_CLIENT_ID')
    AMOCRM_CLIENT_SECRET = os.getenv('AMOCRM_CLIENT_SECRET')
    AMOCRM_LONG_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImI4YWFlMGU1ODA2Nzc1MDAzMjFmMjlhNDYyODI1ZTQ3NjY3MDNkOThjOGE2NDQ1YTNhNTg1M2Y5NDg3YWJjMzU4MGIyNDhmMTAzZjdkZmFmIn0.eyJhdWQiOiJjNDhlMWUwOS04NTVhLTQ3YzItOGQ3Yy0yY2EzM2UxNjhiMWMiLCJqdGkiOiJiOGFhZTBlNTgwNjc3NTAwMzIxZjI5YTQ2MjgyNWU0NzY2NzAzZDk4YzhhNjQ0NWEzYTU4NTNmOTQ4N2FiYzM1ODBiMjQ4ZjEwM2Y3ZGZhZiIsImlhdCI6MTc1MDI2MzQyNSwibmJmIjoxNzUwMjYzNDI1LCJleHAiOjE4NDIzMDcyMDAsInN1YiI6IjEyNjQwMzA2IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNDk0NTU4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiMDBiZDI4ZTMtYTllZS00ZmFiLWI5N2MtYjk0OTdiMDY2MzY4IiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.HvgSDyxs_Lw0opRU7XW95zv1L65Mz-F0XAXdUl_Xwddx6pqP2OXUPXAK-Gr-k85-8nZUV0rtp9fkXHpVh6GpJrKgrnhNCWkv5YHBx29TJj8G-mQEomfrHFv-uzMQt6DY4cktWPAytRqXdloYbv4c_hkMElbqt5M8-fY3GAJY3xLrqzpDtclUh-Hcfyun6-st23-hHdJDWAWCrZxLYK7LcHICZ9XG8EXrx-rNVW_OSRponiYacNAVDW30n-F5hgOdnhrfxAKa-ies35ZakaAHLWtezFl-DP4d0mIQWEVJfeuBAA2LsQng-ct1jbzCnhEGISR4RVviTLufiQrBR9Qp2Q'
    
    @property
    def amocrm_api_url(self) -> str:
        return f'https://{self.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4'

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== AMOCRM КЛАСС =====
class AmoCRMClient:
    """Клиент для работы с amoCRM API"""
    
    def __init__(self):
        self.config = Config()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить HTTP сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Выполнить запрос к API amoCRM"""
        try:
            session = await self._get_session()
            url = f"{self.config.amocrm_api_url}/{endpoint}"
            
            headers = {
                'Authorization': f'Bearer {self.config.AMOCRM_LONG_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            async with session.request(method, url, headers=headers, json=data) as response:
                if response.status == 200 or response.status == 201:
                    result = await response.json()
                    logger.info(f"amoCRM API успешно: {method} {endpoint}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"amoCRM API ошибка {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка запроса к amoCRM: {e}")
            return None
    
    async def create_contact(self, name: str, phone: str, telegram_id: str) -> Optional[int]:
        """Создать контакт в amoCRM"""
        try:
            contact_data = {
                "name": name or f"Клиент {telegram_id}",
                "custom_fields_values": [
                    {
                        "field_id": 33950,  # ID поля для телефона
                        "values": [{"value": phone, "enum_code": "WORK"}]
                    },
                    {
                        "field_id": 33952,  # ID поля для Telegram
                        "values": [{"value": f"@{telegram_id}"}]
                    }
                ]
            }
            
            result = await self._make_request('POST', 'contacts', [contact_data])
            if result and '_embedded' in result and 'contacts' in result['_embedded']:
                contact_id = result['_embedded']['contacts'][0]['id']
                logger.info(f"Контакт создан: ID {contact_id}")
                return contact_id
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания контакта: {e}")
            return None
    
    async def create_lead(self, contact_id: int, message_text: str, telegram_user: str) -> Optional[int]:
        """Создать сделку в amoCRM"""
        try:
            lead_data = {
                "name": f"HVAC заявка от {telegram_user}",
                "price": 5000,  # Предполагаемая стоимость
                "pipeline_id": 8847802,  # ID воронки (стандартная)
                "status_id": 65837170,   # ID статуса "Новая заявка"
                "custom_fields_values": [
                    {
                        "field_id": 1579051,  # ID поля для описания
                        "values": [{"value": message_text[:500]}]  # Ограничиваем длину
                    }
                ],
                "_embedded": {
                    "contacts": [{"id": contact_id}]
                }
            }
            
            result = await self._make_request('POST', 'leads', [lead_data])
            if result and '_embedded' in result and 'leads' in result['_embedded']:
                lead_id = result['_embedded']['leads'][0]['id']
                logger.info(f"Сделка создана: ID {lead_id}")
                return lead_id
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания сделки: {e}")
            return None
    
    async def create_task(self, lead_id: int, telegram_user: str) -> bool:
        """Создать задачу в amoCRM"""
        try:
            task_data = {
                "text": f"Связаться с клиентом {telegram_user} по заявке HVAC",
                "complete_till": int((datetime.now().timestamp() + 3600) * 1000),  # Через час
                "entity_id": lead_id,
                "entity_type": "leads",
                "task_type_id": 1  # Звонок
            }
            
            result = await self._make_request('POST', 'tasks', [task_data])
            if result:
                logger.info(f"Задача создана для сделки {lead_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка создания задачи: {e}")
            return False
    
    async def close(self):
        """Закрыть сессию"""
        if self.session and not self.session.closed:
            await self.session.close()

# ===== TELEGRAM BOT КЛАСС =====
class DSEKBBot:
    """Основной класс бота DS EKB"""
    
    def __init__(self):
        self.config = Config()
        self.amocrm = AmoCRMClient()
        self.application: Optional[Application] = None
    
    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Основная клавиатура бота"""
        keyboard = [
            [KeyboardButton("🔧 AI-диагностика"), KeyboardButton("📋 Заказать услугу")],
            [KeyboardButton("📞 Контакты"), KeyboardButton("❓ FAQ")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда /start"""
        try:
            welcome_text = """
🏢 *Добро пожаловать в DS EKB!*

Мы специализируемся на:
🔧 Обслуживании вентиляции
❄️ Ремонте кондиционеров
🧊 Обслуживании холодильного оборудования

*С использованием искусственного интеллекта!*

Выберите нужную услугу или просто опишите вашу проблему:
            """
            
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=self.get_main_keyboard()
            )
            
            logger.info(f"Пользователь {update.effective_user.username} запустил бота")
            
        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    
    async def handle_ai_diagnostics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка AI-диагностики"""
        try:
            response_text = """
🤖 *AI-Диагностика DS EKB*

Опишите проблему с вашим оборудованием:
• Какой тип оборудования? (вентиляция/кондиционер/холодильник)
• Какие симптомы наблюдаете?
• Когда проблема появилась?

Наш ИИ проанализирует и даст рекомендации!
            """
            
            await update.message.reply_text(
                response_text,
                parse_mode='Markdown',
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка в handle_ai_diagnostics: {e}")
            await update.message.reply_text("Ошибка AI-диагностики. Попробуйте позже.")
    
    async def handle_order_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка заказа услуги"""
        try:
            response_text = """
📋 *Заказ услуги DS EKB*

Для заказа услуги укажите:
• Ваше имя и телефон
• Адрес объекта
• Тип услуги (вентиляция/кондиционер/холодильник)
• Удобное время для визита

Пример: "Иван Петров, +7 922 123-45-67, ул. Ленина 10, ремонт кондиционера, завтра после 14:00"
            """
            
            await update.message.reply_text(
                response_text,
                parse_mode='Markdown',
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка в handle_order_service: {e}")
            await update.message.reply_text("Ошибка заказа услуги. Попробуйте позже.")
    
    async def handle_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка контактов"""
        try:
            contacts_text = """
📞 *Контакты DS EKB*

🏢 *ООО "ДС ЕКБ"*
📍 г. Екатеринбург
📱 +7 922 130-83-65
🌐 ds-ekb.ru

⏰ *Режим работы:*
Пн-Пт: 9:00 - 18:00
Сб: 10:00 - 16:00
Вс: выходной

🚨 *Экстренные вызовы 24/7*
            """
            
            await update.message.reply_text(
                contacts_text,
                parse_mode='Markdown',
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка в handle_contacts: {e}")
            await update.message.reply_text("Ошибка получения контактов. Попробуйте позже.")
    
    async def handle_faq(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка FAQ"""
        try:
            faq_text = """
❓ *Часто задаваемые вопросы*

*Q: Как часто нужно чистить вентиляцию?*
A: Рекомендуется каждые 6-12 месяцев

*Q: Сколько стоит диагностика кондиционера?*
A: AI-диагностика бесплатно, выезд мастера от 1500₽

*Q: Работаете ли с промышленным оборудованием?*
A: Да, обслуживаем любые типы HVAC систем

*Q: Предоставляете ли гарантию?*
A: Да, гарантия на все виды работ от 6 месяцев
            """
            
            await update.message.reply_text(
                faq_text,
                parse_mode='Markdown',
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка в handle_faq: {e}")
            await update.message.reply_text("Ошибка получения FAQ. Попробуйте позже.")
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Извлечь контактную информацию из текста"""
        import re
        
        info = {
            'name': '',
            'phone': '',
            'address': '',
            'service': '',
            'time': ''
        }
        
        # Поиск телефона
        phone_pattern = r'(\+?7[\s\-]?\(?9\d{2}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            info['phone'] = phone_match.group(1)
        
        # Поиск имени (первое слово в начале)
        words = text.split()
        if words:
            info['name'] = words[0]
        
        # Определение типа услуги
        services = ['вентиляц', 'кондиционер', 'холодильн', 'чистка', 'ремонт', 'обслужив']
        for service in services:
            if service in text.lower():
                info['service'] = service
                break
        
        return info
    
    async def process_request(self, user_data: Dict, message_text: str, telegram_user: str) -> Optional[int]:
        """Обработать заявку через amoCRM"""
        try:
            # Создать контакт
            contact_id = await self.amocrm.create_contact(
                name=user_data.get('name', ''),
                phone=user_data.get('phone', ''),
                telegram_id=telegram_user
            )
            
            if not contact_id:
                logger.error("Не удалось создать контакт")
                return None
            
            # Создать сделку
            lead_id = await self.amocrm.create_lead(
                contact_id=contact_id,
                message_text=message_text,
                telegram_user=telegram_user
            )
            
            if not lead_id:
                logger.error("Не удалось создать сделку")
                return None
            
            # Создать задачу
            await self.amocrm.create_task(lead_id, telegram_user)
            
            return lead_id
            
        except Exception as e:
            logger.error(f"Ошибка обработки заявки: {e}")
            return None
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка текстовых сообщений"""
        try:
            message_text = update.message.text
            user = update.effective_user
            telegram_user = user.username or f"id{user.id}"
            
            # Проверка на команды кнопок
            if message_text in ["🔧 AI-диагностика"]:
                await self.handle_ai_diagnostics(update, context)
                return
            elif message_text in ["📋 Заказать услугу"]:
                await self.handle_order_service(update, context)
                return
            elif message_text in ["📞 Контакты"]:
                await self.handle_contacts(update, context)
                return
            elif message_text in ["❓ FAQ"]:
                await self.handle_faq(update, context)
                return
            
            # Обработка как заявки
            await update.message.reply_text(
                "⏳ Принимаем вашу заявку... Создаем сделку в системе...",
                reply_markup=self.get_main_keyboard()
            )
            
            # Извлечь информацию о клиенте
            contact_info = self.extract_contact_info(message_text)
            
            # Обработать заявку через amoCRM
            lead_id = await self.process_request(contact_info, message_text, telegram_user)
            
            if lead_id:
                success_text = f"""
✅ *Заявка принята!*

📋 Номер заявки: #{lead_id}
👤 Клиент: {contact_info.get('name', telegram_user)}
📱 Телефон: {contact_info.get('phone', 'не указан')}

🔄 *Статус:* Новая заявка
⏰ *Время обработки:* до 1 часа

Мы свяжемся с вами в ближайшее время!
                """
                
                await update.message.reply_text(
                    success_text,
                    parse_mode='Markdown',
                    reply_markup=self.get_main_keyboard()
                )
                
                logger.info(f"Заявка {lead_id} успешно создана для {telegram_user}")
                
            else:
                await update.message.reply_text(
                    "⚠️ Заявка принята, но возникли проблемы с системой. Мы обработаем её вручную и свяжемся с вами!",
                    reply_markup=self.get_main_keyboard()
                )
                
                logger.warning(f"Заявка от {telegram_user} принята, но не создана в amoCRM")
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке заявки. Попробуйте позже или позвоните нам: +7 922 130-83-65",
                reply_markup=self.get_main_keyboard()
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"Ошибка бота: {context.error}")
        
        if update and update.message:
            try:
                await update.message.reply_text(
                    "Произошла техническая ошибка. Мы уже работаем над её устранением!",
                    reply_markup=self.get_main_keyboard()
                )
            except Exception:
                pass
    
    async def setup_application(self) -> Application:
        """Настройка приложения бота"""
        # Создать приложение
        application = Application.builder().token(self.config.TELEGRAM_TOKEN).build()
        
        # Добавить обработчики
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Добавить обработчик ошибок
        application.add_error_handler(self.error_handler)
        
        return application
    
    async def start_bot(self) -> None:
        """Запустить бота"""
        try:
            logger.info("Запуск DS EKB бота...")
            
            # Настроить приложение
            self.application = await self.setup_application()
            
            # Инициализировать
            await self.application.initialize()
            
            # Запустить polling
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            logger.info("DS EKB бот успешно запущен!")
            
            # Держать бота запущенным
            await asyncio.Future()  # Бесконечное ожидание
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Очистка ресурсов"""
        try:
            if self.amocrm:
                await self.amocrm.close()
            
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                
            logger.info("Ресурсы очищены")
            
        except Exception as e:
            logger.error(f"Ошибка очистки ресурсов: {e}")

# ===== ГЛАВНАЯ ФУНКЦИЯ =====
async def main():
    """Главная функция запуска"""
    bot = DSEKBBot()
    await bot.start_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
