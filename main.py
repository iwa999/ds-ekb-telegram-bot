from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import handlers
from amocrm_integration import amocrm
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

COLLECT_NAME, COLLECT_PHONE, COLLECT_DESCRIPTION = handlers.COLLECT_NAME, handlers.COLLECT_PHONE, handlers.COLLECT_DESCRIPTION

def main():
    """Основная функция запуска бота"""
    
    # Инициализация amoCRM (используем код авторизации)
    auth_code = "def502004cd15f612c0664a730ba9f08d14f769ab668602e988bcad536a3a87415a27113a48730e701adf128fc9915f74dc52baeb1a19488e781a18a8ec66ba09ff9db707798f32c71c527118510b9ad31339e95743bdbfa9a36a0c84a8dc0493006e1d68716638d4b395bfc2b9dd4fa52d9203e80ef70a3baa7f0a8f2562f50966bdf840aa7a66f99448437348eda2a2b63173e0601f6ec5a4528076285e30e513a5da32bb0401e737a0750316f6ac5dad67ed0c78049bf7526cdd89288cd68bf8d67c614f5bbb1e2323769609c71cece055111a34454ea0ace25eb3286b27634d1133ddc5ba2949a28d46542c5ba6cfdf67f2c592bbf2990eaf7d038a1e73b1f0b6f4dee97ad8362ba5fb9bebba8ae5f1f656f0516e334e5049315a8562a7c1d4caceb1f390011d7fbc5056cb35ab9a82843a02b8b7be3cb65f79a311520f104b2921f9079db8e4e864c297ced317d430eaa3deb0dea4fa10b2dea9f6d931f33ebecaafe2d05cead6047a4f78878154f77c283e9e90ef65b7b495ebb2063e86b4e5a5159294fabf90703349495f273c8d394180aa4db1c6edcc3c2ef5559f933645f232282d42ca848a7a118b3558b1b1ff2f43225d8ba2dceed18107025b465b9900e0460882d9d18039bf26e25a9dd34ede014910216507377a1f81db469e1cfe61a"
    
    # Получаем токены amoCRM
    if amocrm.get_access_token(auth_code):
        logging.info("amoCRM успешно подключен!")
    else:
        logging.error("Ошибка подключения к amoCRM")
    
    # Создаем приложение
    application = Application.builder().token("7437623986:AAFj-sItRC4s889Sop2mglRE7SE2c-drTCY").build()
    
    # Обработчики диалогов для сбора данных
    conversation_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🔧 AI-диагностика$"), handlers.ai_diagnostics),
            MessageHandler(filters.Regex("^📋 Заказать услугу$"), handlers.order_service),
        ],
        states={
            COLLECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.collect_name)],
            COLLECT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.collect_phone)],
            COLLECT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.collect_description)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(conversation_handler)
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), handlers.contacts))
    application.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), handlers.faq))
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
