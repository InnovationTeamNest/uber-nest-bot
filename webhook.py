# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import webapp2
import actions
import actions_booking
import actions_me
import telegram
import dumpable
import secret_data

from inline import inline_handler
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

un_bot = telegram.Bot(secret_data.bot_token)


class WebHookHandler(webapp2.RequestHandler):
    def get(self):
        dispatcher_setup()  # Ogni volta che si carica una nuova versione, bisogna rifare il setup del bot!
        res = un_bot.setWebhook(secret_data.url + secret_data.bot_token)
        if res:
            self.response.write("Webhook set!")
        else:
            self.response.write("Webhook setup failed...")


class UpdateHandler(webapp2.RequestHandler):
    def post(self):  # Gli update vengono forniti da telegram in Json e vanno interpretati
        webhook(telegram.Update.de_json(json.loads(self.request.body), un_bot))
        dumpable.dump_data()


def dispatcher_setup():
    global dispatcher
    dispatcher = Dispatcher(bot=un_bot, update_queue=None, workers=0)

    # Inizio prendendo i dati dal Datastore, altrimenti ce li salvo
    if dumpable.empty_datastore():
        dumpable.dump_data()
    #  else:
    #      dumpable.get_data()

    dispatcher.add_handler(CommandHandler("start", actions.start))
    dispatcher.add_handler(CommandHandler("help", actions.help))
    dispatcher.add_handler(CommandHandler("oggi", actions.oggi))
    dispatcher.add_handler(CommandHandler("domani", actions.domani))
    dispatcher.add_handler(CommandHandler("settimana", actions.settimana))
    dispatcher.add_handler(CommandHandler("prenota", actions_booking.prenota))
    dispatcher.add_handler(CommandHandler("registra", actions.registra))

    dispatcher.add_handler(CommandHandler("me", actions_me.me))

    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, actions.text_filter))
    dispatcher.add_handler(CallbackQueryHandler(inline_handler))


def webhook(update):
    dispatcher.process_update(update)
