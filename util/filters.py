# -*- coding: utf-8 -*-

import logging as log

import telegram


# Questi comandi vengono usati dalla modalità inline per redirezionare correttamente i comandi.
# Il metodo cancel_handler viene usato nel caso in cui si voglia troncare la catena di query.
# Infine, create e separate_callback_data vengono usate per creare le stringhe d'identificazione.


def inline_handler(bot, update):
    from commands import actions_booking, actions_me, actions_money, actions_trips, actions_parking, \
        actions_show_bookings

    # Loggo il contenuto della Callback query
    log.info(update.callback_query.data)

    # Mando un azione di "Sto scrivendo..."
    bot.send_chat_action(chat_id=update.callback_query.from_user.id, action=telegram.ChatAction.TYPING)

    # Nelle callback query, il primo elemento è sempre l'identificatore
    identifier = separate_callback_data(update.callback_query.data)[0]

    try:
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
    except telegram.error.TimedOut as ex:
        log.error(ex)
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text="I server di Telegram sono sotto carico. Riprova tra qualche momento.")
        return
    except telegram.error.BadRequest as ex:
        log.error(ex)
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text="Errore nella richiesta. Per favore, contatta il creatore del bot.")
        return
    except telegram.error.NetworkError as ex:
        log.error(ex)
        bot.answer_callback_query(callback_query_id=update.callback_query.id,
                                  text="I server di Telegram sono sotto carico. Riprova tra qualche momento.")

    # Rimuovo il messaggio di caricamento
    bot.answer_callback_query(callback_query_id=update.callback_query.id)


def cancel_handler(bot, update):
    bot.edit_message_text(chat_id=update.callback_query.from_user.id,
                          message_id=update.callback_query.message.message_id,
                          text="Operazione annullata.",
                          reply_markup=None)


def create_callback_data(*args):
    """Create the callback data associated to each button"""
    return ";".join(str(i) for i in args)


def separate_callback_data(data):
    """ Separate the callback data"""
    return [i for i in data.split(";")]


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
