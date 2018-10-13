# -*- coding: utf-8 -*-

import logging as log
import time

from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

import secret_data
from services import dumpable
from util import filters
from util.common import MAX_ATTEMPTS

bot = Bot(secret_data.bot_token)


def dispatcher_setup():
    global dispatcher
    dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)
    from commands import actions, actions_booking, actions_me, actions_money, actions_parking

    dumpable.get_data()

    # Azioni in partenza da actions.py
    dispatcher.add_handler(CommandHandler("start", actions.start))
    dispatcher.add_handler(CommandHandler("help", actions.help))
    dispatcher.add_handler(CommandHandler("info", actions.info))
    dispatcher.add_handler(CommandHandler("oggi", actions.oggi))
    dispatcher.add_handler(CommandHandler("domani", actions.domani))
    dispatcher.add_handler(CommandHandler("settimana", actions.settimana))
    dispatcher.add_handler(CommandHandler("registra", actions.registra))
    # Azioni dei giorni singoli in partenza da actions.py
    dispatcher.add_handler(CommandHandler("lunedi", actions.lunedi))
    dispatcher.add_handler(CommandHandler("martedi", actions.martedi))
    dispatcher.add_handler(CommandHandler("mercoledi", actions.mercoledi))
    dispatcher.add_handler(CommandHandler("giovedi", actions.giovedi))
    dispatcher.add_handler(CommandHandler("venerdi", actions.venerdi))
    # Azioni in partenza da actions_me
    dispatcher.add_handler(CommandHandler("me", actions_me.me))
    # Azioni in partenza da actions_booking
    dispatcher.add_handler(CommandHandler("prenota", actions_booking.prenota))
    # Azioni in partenza da actions_parking
    dispatcher.add_handler(CommandHandler("parcheggio", actions_parking.parcheggio))
    # Azione supersegreta in partenza da actions_money
    dispatcher.add_handler(CommandHandler("budino", actions_money.edit_money_admin, pass_args=True))
    # Filtri per tutto il resto
    dispatcher.add_handler(MessageHandler(~ Filters.private, filters.public_filter))
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
            log.critical("Failed to initialize Webhook instance")
            log.critical(ex)
