# -*- coding: utf-8 -*-

import json
import webapp2
import actions
import inline
import telegram

from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

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


def dispatcher_setup():
    global dispatcher
    dispatcher = Dispatcher(bot=ccn_bot, update_queue=None, workers=0)

    dispatcher.add_handler(CommandHandler("start", actions.start))
    dispatcher.add_handler(CommandHandler("help", actions.help))
    dispatcher.add_handler(CommandHandler("status", actions.status))
    dispatcher.add_handler(CommandHandler("prenota", actions.prenota))
    dispatcher.add_handler(CommandHandler("registra", actions.registra))

    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, actions.text_filter))
    dispatcher.add_handler(CallbackQueryHandler(inline.inline_handler))


def webhook(update):
    dispatcher.process_update(update)
