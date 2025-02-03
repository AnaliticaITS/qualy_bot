import os
import logging
import requests
import logica_duplicar_casos
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    ConversationHandler    )

from icecream import ic
# from dotenv import load_dotenv
from airflow.scripts.bot_reporte_como_vamos import descargar_como_vamos
from pythonjsonlogger.json import JsonFormatter
from logging.handlers import RotatingFileHandler

#=================================================== Configuración De Logs ========================================================
rotating_handler = RotatingFileHandler(
    "./logs/qualy.json", maxBytes = 5 * 1024 * 1024, backupCount=5
)
json_formatter = JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
)
rotating_handler.setFormatter(json_formatter)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        rotating_handler,
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("qualy_bot")

#=================================================== Declaración De Variables =====================================================
# load_dotenv()
bot_token = os.getenv("BOT_TOKEN") 
id_chat_alkosto = os.getenv("ID_CHAT")
numeros_autorizados = os.getenv("NUMEROS_AUTORIZADOS")
id_chat_analista = os.getenv("ID_CHAT_DEV")
url_api_telegram = "https://api.telegram.org/bot" + bot_token + "/sendMessage?chat_id=" + id_chat_alkosto + "&text="

#======================================================== Logica del Bot ===========================================================
# Estados de la conversación
START_ROUTE, VALIDATION_ROUTE, END_ROUTE = range(3)

# Valores del callback 
ONE, TWO, THREE = range(3)

# Función para descargar la data todos los dias al mismo tiempo que se inicia el bot
def descarga_diaria():
    '''
    Función que administra la descarga automatica diaria del reporte como vamos, dado que el servidor de reporting center tiene una respuesta lenta, si la funcion ***descargar_como_vamos()*** retorna None se llama de manera recursiva hasta completar la descarga
    '''
    downloaded_file, mensaje = descargar_como_vamos()
    if downloaded_file == True:
        logger.info(f"{mensaje}")
        requests.get(url_api_telegram + mensaje)        
    else:
        logger.error(f"{mensaje}")
        requests.get(url_api_telegram + mensaje)        
        descarga_diaria()


# Usamos la declaración de una variable como trigger 
if bot_token:
    descarga_diaria() 
    
    
# Esta función se llamará cada vez que se reciba un mensaje con el comando /duplicar
async def duplicar_casos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:    
    user = update.effective_user    
    if user:
        name = user.first_name
    else:
        name = 'amigo'
    logger.info(f"User {name} started the conversation")     
    contact_keyboard = KeyboardButton(text="Compartir número de teléfono", request_contact=True)
    custom_keyboard = [[contact_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
    message_text = f"Hola _*{name}*_, para _*Duplicar Casos*_ primero debo verificar si tienes autorización para ralizar esta tarea, por favor da clic en el botón para compartir tu número de teléfono"
    await update.message.reply_text(message_text, parse_mode='MarkdownV2', reply_markup=reply_markup)
    
    return START_ROUTE


# Esta función se llamara cada vez que el usuario quiera regresar al menu
async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:    
    reply_message = f"Selecciona una opción?"          
    keyboards = [
        [InlineKeyboardButton("Duplicar por error NOC", callback_data=str(ONE))],
        [InlineKeyboardButton("Duplicar por error service manager", callback_data=str(TWO))],
        [InlineKeyboardButton("Salir", callback_data=str(THREE))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboards)
    await update.callback_query.message.edit_text(reply_message, parse_mode='MarkdownV2', reply_markup=reply_markup)    
    return START_ROUTE
    
 
# Función de seguridad para restringir el acceso al bot
async def verificar_numero_telefonico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contacto = update.message.contact
    numero_telefono = contacto.phone_number             
    if numero_telefono not in numeros_autorizados:
        await update.message.reply_text("Lo siento, no estas autorizado para interactuar conmigo")
    else:
        user = update.effective_user
        name = user.first_name
        reply_message = f"_*{name}*_ en que te puedo ayudar?"
        await update.message.reply_text(reply_message, parse_mode='MarkdownV2')       
        keyboards = [
            [InlineKeyboardButton("Duplicar por error NOC", callback_data=str(ONE))],
            [InlineKeyboardButton("Duplicar por error service manager", callback_data=str(TWO))],
            [InlineKeyboardButton("Salir", callback_data=str(THREE))],
        ]
        reply_markup = InlineKeyboardMarkup(keyboards)
        await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)
        return START_ROUTE
    
   
async def solicitar_im(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.message.edit_text("Ingresa el IM a duplicar con el siguiente formato IMXXXXXX")
    return VALIDATION_ROUTE
    

# LLamamos error service a los casos donde se reportan varios enlaces afectados pero service manager no los duplica
async def duplicar_por_error_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user    
    if user:
        name = user.first_name
    else:
        name = 'amigo' 
    # Llama a otra función y pasa la variable procesada
    respuesta = logica_duplicar_casos.duplicar_enlaces_error_service()
    # Envía un mensaje de vuelta al usuario
    await update.callback_query.message.edit_text(f'Hola {name}: {respuesta}')
    await context.bot.send_message(
        chat_id=id_chat_alkosto, 
        text=(f'Se realizó proceso de duplicación por solicitud de _*{name}*_ con el siguiente resultado: \n\n {respuesta}'), 
        parse_mode='MarkdownV2'
        )
    id_chat_usuario = update.effective_chat.id
    reply_message = f"_*{name}*_ Necesitas algo más?"
    await context.bot.send_message(chat_id=id_chat_usuario,text=reply_message, parse_mode='MarkdownV2')
    keyboards = [
        [InlineKeyboardButton("Mostrar menu", callback_data=str(ONE))],
        [InlineKeyboardButton("Salir", callback_data=str(TWO))],
        ]
    reply_markup = InlineKeyboardMarkup(keyboards)
    await context.bot.send_message(chat_id=id_chat_usuario, text="Selecciona una opción:", reply_markup=reply_markup)
        
    return END_ROUTE 
        

# Llamamos error noc a los casos donde el operador no reporta los enlaces secundarios afectados
async def duplicar_por_error_noc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user    
    if user:
        name = user.first_name
    else:
        name = 'amigo'
    # Guarda el mensaje en una variable
    mensaje_recibido = update.message.text
    # Elimina el comando
    texto_sin_comando = mensaje_recibido.strip()
    # Llama a otra función y pasa la variable procesada
    respuesta = logica_duplicar_casos.duplicar_enlaces_error_noc(texto_sin_comando)
    # Envía un mensaje de vuelta al usuario
    await update.message.reply_text(f'Hola {name}: \n\n {respuesta}')
    # Envia un mensaje al grupo de alkosto
    await context.bot.send_message(
        chat_id=id_chat_alkosto, 
        text=(f'Se realizó proceso de duplicación por solicitud de _*{name}*_ con el siguiente resultado: \n\n {respuesta}'), 
        parse_mode='MarkdownV2'
        )   
    reply_message = f"_*{name}*_ Necesitas algo más?"
    await update.message.reply_text(reply_message, parse_mode='MarkdownV2')
    keyboards = [
        [InlineKeyboardButton("Mostrar menu", callback_data=str(ONE))],
        [InlineKeyboardButton("Salir", callback_data=str(TWO))],
        ]
    reply_markup = InlineKeyboardMarkup(keyboards)
    await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)
        
    return END_ROUTE


async def salir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if user:
        name = user.first_name
    else:
        name = 'amigo'
    await query.answer()
    await query.edit_message_text(text=f"!Hasta pronto {name}!, fue un gusto ayudarte")
    
    return ConversationHandler.END


async def descargar_reporte_como_vamos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Función que administra la descarga por demanda del reporte como vamos, será llamada cada vez que el bot reciba un mensaje directo con el comando /como_vamos
    '''
    query = update.callback_query
    user = update.effective_user
    if user:
        name = user.first_name
    else:
        name = 'amigo'      
    message_text = f"Hola _*{name}*_, te avisare cuando el _*Reporte Como Vamos*_ haya sido descargado"
    await update.message.reply_text(message_text, parse_mode='MarkdownV2')    
    downloaded_file, mensaje = descargar_como_vamos()
    
    if downloaded_file == True:        
        confirmacion_descarga = f"_*{name}*_, te confirmo:\n\n{mensaje}"
        ic(mensaje)
        await update.message.reply_text(confirmacion_descarga, parse_mode='MarkdownV2')
        return
    else:
        confirmacion_descarga = f"_*{name}*_, no se pudo descargar el reporte como vamos:\n\n{mensaje}"
        ic(mensaje)
        await update.message.reply_text(confirmacion_descarga, parse_mode='MarkdownV2')
        descargar_reporte_como_vamos()
        return
        
            
def main():    
    application = Application.builder().token(bot_token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('duplicar', duplicar_casos)],
        states={
            START_ROUTE: [
                MessageHandler(filters.CONTACT, verificar_numero_telefonico),                                
                CallbackQueryHandler(duplicar_por_error_service, pattern="^" + str(TWO) + "$"),
                CallbackQueryHandler(solicitar_im, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(salir, pattern="^" + str(THREE) + "$")               
            ],
            VALIDATION_ROUTE:[
                MessageHandler(filters.Regex("^IM"), duplicar_por_error_noc)
            ],
            END_ROUTE:[       
                CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(salir, pattern="^" + str(TWO) + "$")
                
            ]
        },
        fallbacks=[CommandHandler("duplicar", duplicar_casos)],
    )
           
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("como_vamos", descargar_reporte_como_vamos))
    # application.add_handler(CommandHandler("service", descarga_service))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == '__main__':
    main()

