# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

import telegram
from telegram.error import BadRequest


# Questi comandi vengono usati dalla modalità inline per redirezionare correttamente i comandi.
# Il metodo cancel_handler viene usato come jolly nel caso in cui si voglia troncare la catena di query.
# Infine, create e separate_callback_data vengono usate per creare le stringhe d'identificazione.


def inline_handler(bot, update):
    from commands import actions, actions_booking, actions_me, actions_money

    # Nelle callback query, il primo elemento è sempre l'identificatore
    identifier = separate_callback_data(update.callback_query.data)[0]

    if identifier == "EXIT":  # Caso base usato da molti comandi
        cancel_handler(bot, update)
    elif identifier == "ME_MENU":
        actions_me.me(bot, update)
    elif identifier == "BOOKING_MENU":
        actions_booking.prenota(bot, update)
    elif identifier == "BOOKING":
        actions_booking.booking_handler(bot, update)
    elif identifier == "DELETE_BOOKING":
        actions_booking.delete_booking(bot, update)
    elif identifier == "ME":
        actions_me.me_handler(bot, update)
    elif identifier == "TRIPS":
        actions_me.trips_handler(bot, update)
    elif identifier == "NEWTRIP":
        actions_me.newtrip_handler(bot, update)
    elif identifier == "SHOWBOOKINGS":
        actions.show_bookings(bot, update)
    elif identifier == "MONEY":
        actions_money.check_money(bot, update)
    elif identifier == "EDIT_MONEY":
        actions_money.edit_money(bot, update)
    elif identifier == "NEW_DEBITOR":
        actions_money.new_debitor(bot, update)


def cancel_handler(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    bot.send_message(chat_id=chat_id, text="Operazione annullata.")


def create_callback_data(*arg):
    """ Create the callback data associated to each button"""
    return ";".join(unicode(i) for i in arg)


def separate_callback_data(data):
    """ Separate the callback data"""
    return [unicode(i) for i in data.split(";")]


# Questa classe e questo metodo vengono usate nel caso risposte testuali da parte dell'utente.

class ReplyStatus:
    response_mode = 0


def text_filter(bot, update):
    if ReplyStatus.response_mode == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Digita /help per avere informazioni sui comandi.")
    elif ReplyStatus.response_mode == 1:
        from commands import actions
        actions.response_registra(bot, update)
