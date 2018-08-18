import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

import redis

redis_host = '127.0.0.1'
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

def inicio(bot, update):
    cid = update.message.chat_id
    r.sadd('clientes',cid)
    bot.send_message(chat_id=cid, text="registrado")


def fin(bot, update):
    cid = update.message.chat_id
    r.srem('clientes',cid)
    bot.send_message(chat_id=cid, text="eliminado")



if __name__ == 'main':

    updater = Updater(token='TOKEN')
    dispatcher = updater.dispatcher

    h = CommandHandler('inicio', inicio)
    dispatcher.add_handler(h)

    h = CommandHandler('fin', fin)
    dispatcher.add_handler(h)

    """
    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(echo_handler)
    """

    updater.start_polling()