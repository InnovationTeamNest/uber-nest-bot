# -*- coding: utf-8 -*-
import logging as log
import time
from queue import Queue
from threading import Thread

from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, InlineQueryHandler

import secrets
from util import common


class BotUtils:
    bot = Bot(secrets.bot_token)
    update_queue = Queue()
    dispatcher = Dispatcher(bot, update_queue)
    thread = Thread(target=dispatcher.start, name='dispatcher')

    def __init__(self):
        log.info("BotUtils instance up and running.")

    @staticmethod
    def start_thread():
        BotUtils.thread.start()

    @staticmethod
    def set_webhook():
        BotUtils.bot.setWebhook(secrets.url + secrets.bot_token)


def dispatcher_setup():
    from commands import actions, actions_booking, actions_me, actions_parking, actions_inline
    from util import filters
    from services import dumpable

    # Inizio prendendo i dati da Datastore
    outcome = dumpable.get_data()

    # Se non ci sono dati, provo a inviarli da quanto salvato in secrets.opy
    if not outcome:
        outcome = dumpable.dump_data()

    # Se non ci sono manco quelli, non ha senso far partire il bot
    if not outcome:
        raise SystemError

    # Inizializzo il dispatcher
    BotUtils.start_thread()
    dispatcher = BotUtils.dispatcher

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
    dispatcher.add_handler(CallbackQueryHandler(filters.callback_query_handler))
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(InlineQueryHandler(actions_inline.inline_handler))


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


def error_handler(bot, update, error):
    from telegram.error import (TelegramError, Unauthorized, BadRequest,
                                TimedOut, ChatMigrated, NetworkError)

    try:
        raise error
    except TimedOut as ex:
        log.error(ex)
        if update.callback_query:
            bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                      text="I server di Telegram sono sotto carico. Riprova tra qualche momento.")
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="I server di Telegram sono sotto carico. Riprova tra qualche momento.")

    except BadRequest as ex:
        log.error(ex)
        if update.callback_query:
            bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                      text="Errore nella richiesta. Per favore, contatta il creatore del bot.")
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Errore nella richiesta. Per favore, contatta il creatore del bot.")

    except NetworkError as ex:
        log.error(ex)
        if update.callback_query:
            bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                      text="I server di Telegram sono sotto carico. Riprova tra qualche momento.")
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="I server di Telegram sono sotto carico. Riprova tra qualche momento.")

    except Unauthorized as ex:
        log.error(ex)
        bot.send_message(chat_id=secrets.group_chat_id,
                         text="Avviso automatico: Un utente iscritto a UberNEST ha bloccato"
                              "il Bot. L'utente in questione è pregato di sbloccarlo al più presto.")

    except ChatMigrated as ex:
        pass  # TODO Implement

    except TelegramError as ex:
        log.error(ex)
        if update.callback_query:
            bot.answer_callback_query(callback_query_id=update.callback_query.id)

        bot.send_message(chat_id=update.message.chat_id,
                         text="I server di Telegram hanno riscontrato un errore. Riprova tra qualche "
                              "minuto; se l'errore persiste, contatta il creatore del Bot.")
