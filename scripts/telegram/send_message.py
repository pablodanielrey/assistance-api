
import telegram
from telegram.ext import Updater, MessageHandler, Filters
import sys
import json

def new_member(bot, update):
    print(update)
    for member in update.message.new_chat_members:
        #if member.username == 'ServidoresFceBot':
        update.message.reply_text('Welcome')

def text(bot, update):
    print(update)
    cid = update.message.chat_id
    bot.send_message(chat_id=cid, text='hola')


if __name__ == '__main__':

    config = {}
    with open('/etc/telegram/bot.cfg', 'r') as f:
        config = json.loads(f.read())

    tk = config['token']
    print(tk)

    if len(sys.argv) > 1:
        grupo = config['grupo']

        bot = telegram.Bot(token=tk)
        bot.send_message(chat_id=grupo, text='prueba de mensaje a grupo')

    else:
        updater = Updater(tk)

        updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
        updater.dispatcher.add_handler(MessageHandler(Filters.command, text))
        updater.dispatcher.add_handler(MessageHandler(Filters.text, text))

        updater.start_polling()
        updater.idle()
