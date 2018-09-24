# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging as log
import time

import webapp2
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

import secret_data
from services import dumpable
from util import filters

bot = Bot(secret_data.bot_token)
MAX_ATTEMPTS = 5


class WebHookHandler(webapp2.RequestHandler):
    def get(self):
        dispatcher_setup()  # Ogni volta che si carica una nuova versione, bisogna rifare il setup del bot!
        res = bot.setWebhook(secret_data.url + secret_data.bot_token)
        if res:
            self.response.write("Success!")
        else:
            self.response.write("Webhook setup failed...")
            bot.send_message(chat_id=secret_data.owner_id, text="Errore nel reset del Webhook!")


class UpdateHandler(webapp2.RequestHandler):
    def post(self):  # Gli update vengono forniti da telegram in Json e vanno interpretati
        webhook(Update.de_json(json.loads(self.request.body), bot), 0)
        dumpable.dump_data()


def dispatcher_setup():
    global dispatcher
    dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)
    from commands import actions, actions_booking, actions_me, actions_money

    dumpable.get_data()

    dispatcher.add_handler(CommandHandler("start", actions.start))
    dispatcher.add_handler(CommandHandler("help", actions.help))
    dispatcher.add_handler(CommandHandler("info", actions.info))
    dispatcher.add_handler(CommandHandler("oggi", actions.oggi))
    dispatcher.add_handler(CommandHandler("domani", actions.domani))
    dispatcher.add_handler(CommandHandler("settimana", actions.settimana))
    dispatcher.add_handler(CommandHandler("registra", actions.registra))

    dispatcher.add_handler(CommandHandler("lunedi", actions.lunedi))
    dispatcher.add_handler(CommandHandler("martedi", actions.martedi))
    dispatcher.add_handler(CommandHandler("mercoledi", actions.mercoledi))
    dispatcher.add_handler(CommandHandler("giovedi", actions.giovedi))
    dispatcher.add_handler(CommandHandler("venerdi", actions.venerdi))

    dispatcher.add_handler(CommandHandler("me", actions_me.me))

    dispatcher.add_handler(CommandHandler("prenota", actions_booking.prenota))

    dispatcher.add_handler(CommandHandler("budino", actions_money.edit_money_admin, pass_args=True))

    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, filters.text_filter))
    dispatcher.add_handler(CallbackQueryHandler(filters.inline_handler))


def webhook(update, counter):
    try:
        dispatcher.process_update(update)
    except Exception as ex:
        dispatcher_setup()
        bot.setWebhook(secret_data.url + secret_data.bot_token)
        if counter < MAX_ATTEMPTS:
            time.sleep(2 ** counter)
            webhook(update, counter + 1)
        else:
            bot.send_message(chat_id=secret_data.owner_id, text="ERRORE! Impossibile ripristinare lo stato del bot.")
            log.critical("Failed to initialize Webhook instance" + ex.message)
