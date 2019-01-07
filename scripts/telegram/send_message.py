
import telegram
from telegram.ext import Updater, MessageHandler, Filters
import sys

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

    tk = sys.argv[1]

    if len(sys.argv) > 2:
        bot = telegram.Bot(token=tk)
        grupo = sys.argv[2]
        bot.send_message(chat_id=grupo, text='prueba de mensaje a grupo')

    else:

        updater = Updater(tk)

        updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
        updater.dispatcher.add_handler(MessageHandler(Filters.command, text))
        updater.dispatcher.add_handler(MessageHandler(Filters.text, text))

        updater.start_polling()
        updater.idle()
