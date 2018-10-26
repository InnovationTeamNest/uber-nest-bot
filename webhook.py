# -*- coding: utf-8 -*-
import logging as log
import time

from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

import secrets
from util import common

bot = Bot(secrets.bot_token)


def dispatcher_setup():
    from commands import actions, actions_booking, actions_me, actions_parking
    from util import filters
    from services import dumpable

    # Inizializzo il dispatcher
    global dispatcher
    dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0)

    # Inizio prendendo i dati da Datastore
    outcome = dumpable.get_data()

    # Se non ci sono dati, provo a inviarli da quanto salvato in secrets.opy
    if not outcome:
        outcome = dumpable.dump_data()

    # Se non ci sono manco quelli, non ha senso far partire il bot
    if not outcome:
        raise SystemError

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

    # Filtri per tutto il resto
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, filters.text_filter))
    dispatcher.add_handler(CallbackQueryHandler(filters.inline_handler))

    return bot.setWebhook(secrets.url + secrets.bot_token)


def process(update, counter=0):
    try:
        dispatcher.process_update(update)
    except NameError as ex:
        dispatcher_setup()
        if counter < common.MAX_ATTEMPTS:
            time.sleep(2 ** counter)
            process(update, counter + 1)
        else:
            log.critical("Failed to initialize Webhook instance")
            log.critical(ex)
    except Exception as ex:
        log.error("An exception occurred during handling of the update.")
        log.critical(ex)
