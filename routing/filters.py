# -*- coding: utf-8 -*-
import logging as log

import telegram

from data import secrets
from data.data_api import all_users


#
# In questo file sono presenti svariati metodi adibiti alla gestione dei comandi che non siano esplicitamente
# con lo slash oppure inline, ovvero callback query, messaggi di cancellazione, errori e messaggi in chat pubbliche.
#

def create_callback_data(*args):
    """Crea una stringa a partire dai vlaori (arbitrari) in entrata, che verranno separati da ;"""
    return ";".join(str(i) for i in args)


def separate_callback_data(data):
    """Separa i dati in entrata"""
    return [i for i in data.split(";")]


def callback_query_handler(bot, update):
    from commands import actions_booking, actions_me, actions_money, actions_trips, actions_parking, \
        actions_show_bookings

    chat_id = str(update.callback_query.from_user.id)

    if chat_id not in all_users():
        # Gli utenti non registrati a sistema non possono usare i bottoni in ogni caso
        bot.send_message(chat_id=chat_id,
                         text="Attenzione! Stai cercando di effettuare un operazione riservata"
                              " agli utenti registrati. Per favore, registrati con /registra.")
    else:
        # Mando un azione di "Sto scrivendo..."
        bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)

        # Nelle callback query, il primo elemento è sempre l'identificatore
        identifier = separate_callback_data(update.callback_query.data)[0]

        # Caso base usato da molti comandi
        if identifier == "EXIT":
            cancel_handler(bot, update)
        # Azione alternativa per /me
        elif identifier == "ME_MENU":
            actions_me.me(bot, update)
        # Azione alternativa per /prenota
        elif identifier == "BOOKING_MENU":
            actions_booking.prenota(bot, update)
        # Azioni in partenza da /prenota
        elif identifier == "BOOKING":
            actions_booking.booking_handler(bot, update)
        elif identifier == "EDIT_BOOK":
            actions_booking.edit_booking(bot, update)
        elif identifier == "INFO_BOOK":
            actions_booking.info_booking(bot, update)
        elif identifier == "ALERT_USER":
            actions_booking.alert_user(bot, update)
        # Azione in partenxza da /parcheggio
        elif identifier == "CONFIRM_PARK":
            actions_parking.confirm_parking(bot, update)
        elif identifier == "SEND_LOCATION":
            actions_parking.send_location(bot, update)
        # Azione in partenza da /prenota e da /settimana /lunedi etc
        elif identifier == "SHOW_BOOKINGS":
            actions_show_bookings.show_bookings(bot, update)
        # Azioni in partenza da /me -> trips
        elif identifier == "TRIPS":
            actions_trips.trips_handler(bot, update)
        elif identifier == "ADD_PASS":
            actions_trips.add_passenger(bot, update)
        elif identifier == "ADD_TRIP":
            actions_trips.add_trip(bot, update)
        # Azioni in partenza da /me
        elif identifier == "ME":
            actions_me.me_handler(bot, update)
        elif identifier == "MONEY":
            actions_money.check_money(bot, update)
        elif identifier == "EDIT_MONEY":
            actions_money.edit_money(bot, update)
        elif identifier == "NEW_DEBITOR":
            actions_money.new_debitor(bot, update)

    # Rimuovo il messaggio di caricamento
    bot.answer_callback_query(callback_query_id=update.callback_query.id)


def cancel_handler(bot, update):
    bot.edit_message_text(chat_id=update.callback_query.from_user.id,
                          message_id=update.callback_query.message.message_id,
                          text="Operazione annullata.",
                          reply_markup=None)


# Questa classe e questo metodo vengono usate nel caso risposte testuali da parte dell'utente.
class ReplyStatus:
    response_mode = 0


def text_filter(bot, update):
    """Per aggiungere un nuovo metodo di risposta testuale, mettere qui l'eventuale redirect"""
    if ReplyStatus.response_mode == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Digita /help per avere informazioni sui comandi.")
    elif ReplyStatus.response_mode == 1:
        from commands import actions
        actions.response_registra(bot, update)


def public_filter(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Per iniziare, scrivi un messaggio privato a @ubernestbot.")


# Questo metodo riceve tutti gli errori del programma relativo a Telegram
# e li gestisce. In linea di massima viene mandato un messaggio all'utente oppure viene risposta
# la relativa query, e poi l'eccezione viene loggata.
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
        log.error(ex)

    except TelegramError as ex:
        log.error(ex)
        if update.callback_query:
            bot.answer_callback_query(callback_query_id=update.callback_query.id)

        bot.send_message(chat_id=update.message.chat_id,
                         text="I server di Telegram hanno riscontrato un errore. Riprova tra qualche "
                              "minuto; se l'errore persiste, contatta il creatore del Bot.")
