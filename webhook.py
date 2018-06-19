# -*- coding: utf-8 -*-
import json

import telegram
import webapp2
import actions


from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

import inline
from secrets import bot_token, url

ccn_bot = telegram.Bot(bot_token)


class WebHookHandler(webapp2.RequestHandler):
    def get(self):
        dispatcher_setup()  # Ogni volta che si carica una nuova versione, bisogna rifare il setup del bot!
        res = ccn_bot.setWebhook(url + bot_token)
        if res:
            self.response.write("Webhook set!")
        else:
            self.response.write("Webhook setup failed...")  # TODO Add more information about failed setup...


class UpdateHandler(webapp2.RequestHandler):
    def post(self):  # Gli update vengono forniti da telegram in Json e vanno interpretati
        webhook(telegram.Update.de_json(json.loads(self.request.body), ccn_bot))


# Ogni comando necessita di un CommandHandler appropriato,
# che prende in ingresso un metodo con due parametri, bot e update
def dispatcher_setup():
    global dispatcher
    dispatcher = Dispatcher(bot=ccn_bot, update_queue=None, workers=0)

    dispatcher.add_handler(CommandHandler("turni", actions.turni))
    dispatcher.add_handler(CommandHandler("prenota", actions.prenota))
    dispatcher.add_handler(CommandHandler("emergenza", actions.emergenza))
    dispatcher.add_handler(CommandHandler("registra", actions.registra))
    dispatcher.add_handler(CallbackQueryHandler(inline.inline_handler))


def webhook(update):
    dispatcher.process_update(update)
