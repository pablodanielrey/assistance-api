import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

import datetime
import os

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton

import redis

redis_host = os.environ.get('TELEGRAM_BOT_REDIS')
redis_port = int(os.environ.get('TELEGRAM_BOT_REDIS_PORT', 6379))
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

bot_name = os.environ.get('TELEGRAM_BOT_NAME')
bot_username = os.environ.get('TELEGRAM_BOT_USERNAME')
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

print('Iniciando bot usando token : {}'.format(TOKEN))

def inicio(bot, update):
    cid = update.message.chat_id
    iniciar_keyboard = KeyboardButton(text="Recibir eventos", request_contact=True, request_location=True)
    finalizar_keyboard = InlineKeyboardButton(text="No recibir eventos", callback_data='2')
    reply_markup = ReplyKeyboardMarkup([[iniciar_keyboard, finalizar_keyboard]])
    bot.send_message(chat_id=cid, text='Debe seleccionar si desea recibir los eventos o no', reply_markup=reply_markup)


def fin(bot, update):
    cid = update.message.chat_id
    r.srem('clientes',cid)
    bot.send_message(chat_id=cid, text="No recibirá mas eventos")
    logging.info('cliente desregistrado {}'.format(cid))

def contact_callback(bot, update):
    cid = update.message.chat_id
    r.sadd('clientes',cid)

    contact = update.effective_message.contact
    logging.info('contacto registrado')
    logging.info(contact)
    phone = contact.phone_number
    logging.info(phone)

def text_callback(bot, update):
    fin(bot, update)    

def callback_minute(bot, job):
    logs = r.lpop('marcaciones')
    if logs:
        for l in logs:
            cids = r.smembers('clientes')
            for cid in cids:
                bot.send_message(chat_id=cid, text='{}'.format(l))
                logging.info('enviando {} a {}'.format(l,cid))
   


if __name__ == '__main__':

    updater = Updater(token=TOKEN)
    job_minute = updater.job_queue.run_repeating(callback_minute, interval=10, first=0)
    dispatcher = updater.dispatcher

    h = CommandHandler('start', inicio)
    dispatcher.add_handler(h)

    h = CommandHandler('end', fin)
    dispatcher.add_handler(h)

    dispatcher.add_handler(MessageHandler(Filters.contact, contact_callback))
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