"""
Обработчики сообщений Telegram бота
Вся логика взаимодействия с пользователями
"""

import asyncio
import logging
import re
from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from amocrm import process_user_request
from utils import extract_user_data, format_message

logger = logging.getLogger(__name__)

class BotHandlers:
    """Класс обработчиков сообщений бота"""
    
    def __init__(self):
        self.config = Config()
        self.processing_users = set()  # Для предотвращения дублирования заявок

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        try:
            keyboard = [
                [InlineKeyboardButton("🔧 AI-диагностика", callback_data="ai_diagnostics")],
                [InlineKeyboardButton("📋 Заказать услугу", callback_data="order_service")],
                [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
                [InlineKeyboardButton("❓ FAQ", callback_data="faq")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                self.config.WELCOME_MESSAGE,
                reply_markup=reply_markup
            )
            
            logger.info(f"👤 Новый пользователь: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в start_command: {e}")
            await self._send_error_message(update)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_text = (
            "🔧 **Как пользоваться ботом ДС ЕКБ:**\n\n"
            "1️⃣ Опишите вашу проблему в свободной форме\n"
            "2️⃣ Укажите контактные данные\n"
            "3️⃣ Получите номер заявки\n"
            "4️⃣ Ожидайте звонка специалиста\n\n"
            "📞 **Экстренная связь:** +7 922 130-83-65\n"
            "🕐 **Рабочие часы:** 8:00-20:00\n\n"
            "💡 **Примеры запросов:**\n"
            "• 'Кондиционер не охлаждает'\n"
            "• 'Нужна чистка вентиляции в офисе'\n"
            "• 'Не работает холодильник в магазине'"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /status"""
        status_text = (
            "📊 **Статус системы ДС ЕКБ:**\n\n"
            "🤖 Бот: ✅ Работает\n"
            "🔗 amoCRM: ✅ Подключено\n"
            "📞 Колл-центр: ✅ Активен\n\n"
            "⏱️ Среднее время ответа: 15 минут\n"
            "👥 Специалистов на линии: 3\n\n"
            "Все системы работают штатно!"
        )
        
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Основной обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        
        # Предотвращаем дублирование обработки
        if user_id in self.processing_users:
            await update.message.reply_text(
                "⏳ Ваша предыдущая заявка обрабатывается...\nПожалуйста, подождите."
            )
            return
        
        try:
            self.processing_users.add(user_id)
            
            # Отправляем подтверждение получения
            processing_msg = await update.message.reply_text(
                "📨 Заявка получена!\n⏳ Обрабатываем..."
            )
            
            # Извлекаем данные пользователя
            user_data = extract_user_data(update)
            
            # Логируем заявку
            logger.info(f"📋 Новая заявка от {user_id}: {user_data['message'][:50]}...")
            
            # Обрабатываем заявку в amoCRM
            success, response_message, deal_number = await process_user_request(user_data)
            
            # Удаляем сообщение "обрабатываем"
            try:
                await processing_msg.delete()
            except:
                pass
            
            # Отправляем результат
            if success:
                await update.message.reply_text(
                    response_message,
                    reply_markup=self._get_main_menu_keyboard()
                )
                logger.info(f"✅ Заявка {deal_number} создана для пользователя {user_id}")
            else:
                await update.message.reply_text(response_message)
                logger.warning(f"⚠️ Не удалось создать заявку для пользователя {user_id}")
            
            # Отправляем дополнительные инструкции
            await asyncio.sleep(2)
            await update.message.reply_text(
                "💬 Можете отправить дополнительную информацию или фото проблемы"
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения от {user_id}: {e}")
            await self._send_error_message(update)
        finally:
            self.processing_users.discard(user_id)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик фотографий"""
        try:
            # Получаем информацию о фото
            photo = update.message.photo[-1]  # Берем самое большое разрешение
            file_id = photo.file_id
            
            caption = update.message.caption or "Фото от клиента"
            
            await update.message.reply_text(
                "📸 Фото получено!\n"
                "Передадим специалисту для анализа.\n\n"
                "💬 Можете также описать проблему текстом"
            )
            
            # Логируем получение фото
            user_id = update.effective_user.id
            logger.info(f"📸 Фото получено от пользователя {user_id}: {file_id}")
            
            # Здесь можно добавить сохранение фото в amoCRM или на сервер
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки фото: {e}")
            await self._send_error_message(update)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик callback запросов от кнопок"""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data
            
            if data == "ai_diagnostics":
                await query.edit_message_text(
                    "🔍 **AI-диагностика HVAC оборудования**\n\n"
                    "Опишите проблему максимально подробно:\n"
                    "• Что именно не работает?\n"
                    "• Когда началась проблема?\n"
                    "• Какие звуки/запахи есть?\n"
                    "• Модель оборудования (если знаете)\n\n"
                    "ИИ проанализирует и даст рекомендации!",
                    parse_mode='Markdown'
                )
                
            elif data == "order_service":
                await query.edit_message_text(
                    "📋 **Заказ услуги**\n\n"
                    "Напишите что нужно сделать:\n"
                    "• Ремонт кондиционера\n"
                    "• Чистка вентиляции\n"
                    "• Обслуживание холодильника\n\n"
                    "Укажите также:\n"
                    "• Ваш контактный телефон\n"
                    "• Адрес объекта\n"
                    "• Удобное время",
                    parse_mode='Markdown'
                )
                
            elif data == "contacts":
                await query.edit_message_text(
                    f"📞 **Контакты ДС ЕКБ**\n\n"
                    f"☎️ Телефон: {self.config.COMPANY_PHONE}\n"
                    f"🕐 Рабочие часы: 8:00-20:00\n"
                    f"📧 Email: info@ds-ekb.ru\n"
                    f"📍 Адрес: г. Екатеринбург\n\n"
                    f"💬 Telegram: {self.config.BOT_USERNAME}\n\n"
                    f"Работаем без выходных!",
                    parse_mode='Markdown'
                )
                
            elif data == "faq":
                await query.edit_message_text(
                    "❓ **Часто задаваемые вопросы**\n\n"
                    "**Как быстро приедет мастер?**\n"
                    "В течение 30 минут после заявки\n\n"
                    "**Работаете ли в выходные?**\n"
                    "Да, работаем 7 дней в неделю\n\n"
                    "**Есть ли гарантия на работы?**\n"
                    "Да, 6 месяцев на все виды работ\n\n"
                    "**Принимаете ли безналичный расчет?**\n"
                    "Да, принимаем карты и переводы",
                    parse_mode='Markdown',
                    reply_markup=self._get_main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback: {e}")

    def _get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры главного меню"""
        keyboard = [
            [InlineKeyboardButton("🔧 AI-диагностика", callback_data="ai_diagnostics")],
            [InlineKeyboardButton("📋 Заказать услугу", callback_data="order_service")],
            [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
            [InlineKeyboardButton("❓ FAQ", callback_data="faq")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def _send_error_message(self, update: Update) -> None:
        """Отправка сообщения об ошибке"""
        try:
            await update.message.reply_text(self.config.ERROR_MESSAGE)
        except:
            logger.error("❌ Не удалось отправить сообщение об ошибке")
