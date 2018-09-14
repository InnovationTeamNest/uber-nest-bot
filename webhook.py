# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import telegram
import webapp2
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

import actions
import actions_booking
import actions_me
import dumpable
import inline
import secret_data

bot = telegram.Bot(secret_data.bot_token)


class WebHookHandler(webapp2.RequestHandler):
    def get(self):
        dispatcher_setup()  # Ogni volta che si carica una nuova versione, bisogna rifare il setup del bot!
        res = bot.setWebhook(secret_data.url + secret_data.bot_token)
        if res:
            self.response.write("Success!")
            bot.send_message(chat_id=secret_data.owner_id, text="Webhook resettato con successo!")
        else:
            self.response.write("Webhook setup failed...")


class UpdateHandler(webapp2.RequestHandler):
    def post(self):  # Gli update vengono forniti da telegram in Json e vanno interpretati
        webhook(telegram.Update.de_json(json.loads(self.request.body), bot))
        dumpable.dump_data()


def dispatcher_setup():
    global dispatcher
    dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)

    dumpable.get_data()

    dispatcher.add_handler(CommandHandler("start", actions.start))
    dispatcher.add_handler(CommandHandler("help", actions.help))
    dispatcher.add_handler(CommandHandler("info", actions.info))
    dispatcher.add_handler(CommandHandler("oggi", actions.oggi))
    dispatcher.add_handler(CommandHandler("domani", actions.domani))
    dispatcher.add_handler(CommandHandler("settimana", actions.settimana))
    dispatcher.add_handler(CommandHandler("registra", actions.registra))

    dispatcher.add_handler(CommandHandler("me", actions_me.me))
    dispatcher.add_handler(CommandHandler("prenota", actions_booking.prenota))

    dispatcher.add_handler(CommandHandler("lunedi", actions.lunedi))
    dispatcher.add_handler(CommandHandler("martedi", actions.martedi))
    dispatcher.add_handler(CommandHandler("mercoledi", actions.mercoledi))
    dispatcher.add_handler(CommandHandler("giovedi", actions.giovedi))
    dispatcher.add_handler(CommandHandler("venerdi", actions.venerdi))

    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, actions.text_filter))
    dispatcher.add_handler(CallbackQueryHandler(inline.inline_handler))


def webhook(update):
    dispatcher.process_update(update)
