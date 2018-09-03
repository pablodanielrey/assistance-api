"""
    Implementa un bot básico de notificaciones de telegram.
    claves redis a tener en cuenta:

    telegram_{uid} : {
                        'notificar': 0|1
                        't_telefono': ..
                        't_nombre': ..
                        't_apellido': ..
                        't_usuario_id': ..
                        't_chat_id': ..
                        'u_dni': ..
                        'u_nombre': ..
                        'u_apellido': ..
                        'u_correo': ..
                    }                       ---> datos del usuario chateando con el bot

    t_chat_id_{} : {
                        'uid': uid 
                    }                      ---> para asociar los datos de un chat con un usuario


    t_auth_{} : {                          ---> codigo de autorizacion   
                    'chat_id': ...         ---> chat a autorizar
                }


    t_athorized : [chat_id]

    telegram : [{
            'dni': dni,
            'usuario': usuario,
            'log': marcacion
            }]                              ---> conjunto de las marcaciones sincronizadas en el modelo a notificar

"""

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

import hashlib
import datetime
from dateutil import parser
import pytz
import os
import json

from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram.ext import MessageHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from telegram import Contact
from telegram import ParseMode

import redis

redis_host = os.environ.get('TELEGRAM_BOT_REDIS')
redis_port = int(os.environ.get('TELEGRAM_BOT_REDIS_PORT', 6379))
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

bot_name = os.environ.get('TELEGRAM_BOT_NAME')
bot_username = os.environ.get('TELEGRAM_BOT_USERNAME')
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

WEB_URL = os.environ.get('ASSISTANCE_URL', 'http://localhost')

print('Iniciando bot usando token : {}'.format(TOKEN))

def inicio(bot, update, args=[]):
    cid = update.message.chat_id
    logging.info('cliente conectado {}'.format(cid))

    k = 't_chat_id_{}'.format(cid)
    if not r.hexists(k,'uid'):
        code = hashlib.sha1('{}_{}'.format(datetime.datetime.now(),cid).encode('utf-8')).hexdigest()[:5]
        kc = 't_auth_{}'.format(code)
        r.hset(kc,'chat_id',cid)

        template = """
<pre>
Por favor ingrese a la aplicación web de asistencia y escriba el siguente codigo
en la seccion de Telegram.
Codigo: {}
</pre>
""".format(code)

        logging.info(template)
        bot.send_message(chat_id=cid, text=template, parse_mode=ParseMode.HTML)
        return


        url = '{}/telegram/{}'.format(WEB_URL, code)
        template = """
<pre>
Para activar su usuario por favor haga click
</pre>
<a href="{}">aqui</a>
""".format(url)
        
        logging.info('enviando')
        logging.info(template)
        bot.send_message(chat_id=cid, text=template, parse_mode=ParseMode.HTML)
        return


    """
        Ya tenemos asociado el chat_id con un usuario.
        por lo que se continua con el proceso de registro del usuario.
    """

    uid = r.hget(k,'uid')
    kt = 'telegram_{}'.format(uid)
    usr = r.hgetall(kt)
    if not usr:
        ''' situación anómala. desregistro completamente al usuario, el chat_id '''
        r.hdel(k,'uid')
        bot.send_message(chat_id=cid, text='Error. Por favor regítrese nuevamente')
        return

    bot.send_message(chat_id=cid, text='Bienvenido {} {}'.format(usr['u_nombre'], usr['u_apellido']))
    
    telefono = """
<pre>
Para poder continuar necesitamos verificar su número telefónico.
Por favor haga click en el siguiente botón.
Gracias.
</pre>"""
    bot.send_message(
        chat_id=cid,
        text=telefono, 
        parse_mode=ParseMode.HTML, 
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text='Enviar número', request_contact=True, request_location=True)]])
        )

def contact_callback(bot, update):
    ''' recibo la info del contacto. respuesta al mensaje anterior '''
    cid = update.effective_message.chat_id
    contact = update.effective_message.contact
    
    uid = r.hget('t_chat_id_{}'.format(cid), 'uid')
    if not uid:
        bot.send_message(chat_id=cid, text='Debe ingresar por la aplicación')
        return

    k = 'telegram_{}'.format(uid)
    tusr = r.hgetall(k)
    if not tusr:
        bot.send_message(chat_id=cid, text='Debe ingresar por la aplicación')
        return

    r.hset(k, 't_telefono', contact.phone_number)
    r.hset(k, 't_nombre', contact.first_name)
    r.hset(k, 't_apellido', contact.last_name)
    r.hset(k, 't_usuario_id', contact.user_id)

    _enviar_seleccion_notificar(bot, cid)

def _enviar_seleccion_notificar(bot, cid):
    iniciar_keyboard = InlineKeyboardButton(text="Recibir notificaciones", callback_data='1')
    finalizar_keyboard = InlineKeyboardButton(text="No recibir notificaciones", callback_data='2')
    reply_markup = ReplyKeyboardMarkup([[iniciar_keyboard, finalizar_keyboard]])
    bot.send_message(chat_id=cid, text='Debe seleccionar si desea recibir los eventos o no', reply_markup=reply_markup)

def button(bot, update):
    query = update.callback_query
    opcion = query.data
    cid = query.message.chat_id

    uid = r.hget('t_chat_id_{}'.format(cid), 'uid')
    if not uid:
        bot.send_message(chat_id=cid, text='Debe ingresar por la aplicación')
        return

    k = 'telegram_{}'.format(uid)
    if '1' == opcion:
        r.hset(k,'notificar',1)
        bot.sent_message(chat_id=cid, text='Notificacion habilitdas')
        return

    if '2' == opcion:
        r.hset(k,'notificar',0)
        bot.sent_message(chat_id=cid, text='Notificaciones desabilitadas')
        return

    bot.sent_message(chat_id=cid, text='No entiendo')

def status(bot, update):
    cid = update.message.chat_id
    if not r.hexists('t_chat_id_{}'.format(cid), 'uid'):
        bot.send_message(chat_id=cid, text='No permitido')
        return

    for k in r.keys('*'):
        bot.send_message(chat_id=cid, text=k)
        logging.info(k)
        bot.send_message(chat_id=cid, text='{}'.format(r.hgetall(k)))

def text_callback(bot, update):
    cid = update.message.chat_id
    bot.send_message(chat_id=cid, text='No entiendo')

def _obtener_correo(mails):
    if not mails:
        return ""
    for m in mails:
        if 'econo.unlp.edu.ar' in m['email'] and not m['eliminado'] and m['confirmado']:
            return m['email']
    return ""

def _obtener_usr(uid):
    k = 'telegram_{}'.format(uid)
    return r.hgetall(k)

def _procesar_cola_marcaciones(bot, timezone=None):
    if not timezone:
        timezone = pytz.timezone('America/Argentina/Buenos_Aires')
    log = True
    while log:
        log = r.spop('telegram')
        if log:
            l = json.loads(log)
            logging.info('enviando {}'.format(l))
            usr = _obtener_usr(log['usuario']['id'])
            if usr['notificar'] >= 1:
                cid = usr['t_chat_id']
                fecha_hora = parser.parse(l['log']['marcacion']).astimezone(timezone)
                dni = l['usuario']['dni']
                nombre = l['usuario']['nombre']
                apellido = l['usuario']['apellido']

                template = """
<pre>
Dni: {}
Nombre: {}
Apellido: {}
Fecha: {}
Hora: {}
Tipo Marcación: {}
Reloj: {}
Correo: {}
</pre>
                """.format(dni, nombre, apellido,                    
                    fecha_hora.date(),
                    fecha_hora.time(),
                    l['log']['tipo'],
                    l['log']['dispositivo_id'],
                    #_obtener_correo(l['usuario']['mails']))
                    "en la nueva versión"
                )

                logging.info('Notificando')
                logging.info(usr)
                logging.info(template)

                bot.send_message(chat_id=cid, text='{}'.format(template), parse_mode=ParseMode.HTML)
            else:
                logging.info('cliente no quiere ser notificado')
                logging.info(usr)


def _procesar_cola_autorizacion(bot):
    uid = True
    while uid:
        uid = r.spop('t_authorized')
        if not uid:
            continue
        usr = r.hgetall('telegram_{}'.format(uid))
        cid = usr['t_chat_id']
        template = "Bién!!! {} {} se ha registrado correctamente".format(usr['u_nombre'],usr['u_apellido'])
        logging.info(template)
        bot.send_message(chat_id=cid, text=template)
    

def callback_minute(bot, job):
    timezone = pytz.timezone('America/Argentina/Buenos_Aires')
    _procesar_cola_autorizacion(bot)
    _procesar_cola_marcaciones(bot, timezone)


if __name__ == '__main__':

    updater = Updater(token=TOKEN)
    job_minute = updater.job_queue.run_repeating(callback_minute, interval=60, first=0)
    dispatcher = updater.dispatcher

    h = CommandHandler('start', inicio)
    dispatcher.add_handler(h)

    h = CommandHandler('status', status)
    dispatcher.add_handler(h)    

    dispatcher.add_handler(MessageHandler(Filters.contact, contact_callback))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text, text_callback))


    """
    dispatcher.add_handler(CommandHandler("inicio", inicio,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    """


    """
    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(echo_handler)
    """

    updater.start_polling()
    updater.idle()