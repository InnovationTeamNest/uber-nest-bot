# -*- coding: utf-8 -*-
import logging as log
import time
from queue import Queue
from threading import Thread

from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, InlineQueryHandler

import secrets
from util import common, inline
from util.filters import error_handler


class BotUtils:
    bot = Bot(secrets.bot_token)
    update_queue = Queue()
    dispatcher = Dispatcher(bot, update_queue)
    thread = Thread(target=dispatcher.start, name='dispatcher')

    def __init__(self):
        log.info("BotUtils instance up and running.")

    @staticmethod
    def start_thread():
        try:
            BotUtils.thread.start()
        except RuntimeError as ex:
            log.critical(ex)
            log.critical("Tried to start an active Thread!")

    @staticmethod
    def set_webhook():
        BotUtils.bot.setWebhook(secrets.url + secrets.bot_token)


def dispatcher_setup():
    from commands import actions, actions_booking, actions_me, actions_parking
    from util import filters
    from services import dumpable

    # Inizio prendendo i dati da Datastore
    outcome = dumpable.get_data()

    # Se non ci sono dati, provo a inviarli da quanto salvato in secrets.py
    if not outcome:
        outcome = dumpable.dump_data()

    # Se non ci sono manco quelli, non ha senso far partire il bot
    if not outcome:
        raise SystemError

    # Inizializzo il dispatcher
    BotUtils.start_thread()
    dispatcher = BotUtils.dispatcher

    # Filtri per tutto il resto
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(CallbackQueryHandler(filters.callback_query_handler))
    dispatcher.add_handler(InlineQueryHandler(inline.inline_handler))

    dispatcher.add_handler(MessageHandler(~ Filters.private, filters.public_filter))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, filters.text_filter))

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


def process(update, counter=0):
    try:
        BotUtils.update_queue.put(update)
    except NameError as ex:
        dispatcher_setup()
        if counter < common.MAX_ATTEMPTS:
            time.sleep(2 ** counter)
            process(update, counter + 1)
        else:
            log.critical("Failed to initialize Dispatcher instance")
            log.critical(ex)
