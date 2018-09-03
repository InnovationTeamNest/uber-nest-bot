# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import telegram

import actions
import actions_booking
import actions_me
import money


def inline_handler(bot, update):
    # Nelle callback query, il primo elemento è sempre l'identificatore
    identifier = separate_callback_data(update.callback_query.data)[0]

    if identifier == "BOOKING":
        actions_booking.booking_handler(bot, update)
    elif identifier == "DELETEBOOKING":
        actions_booking.delete_booking(bot, update)
    elif identifier == "ME":
        actions_me.me_handler(bot, update)
    elif identifier == "TRIPS":
        actions_me.trips_handler(bot, update)
    elif identifier == "NEWTRIP":
        actions_me.newtrip_handler(bot, update)
    elif identifier == "SHOWBOOKINGS":
        actions.show_bookings(bot, update)
    elif identifier == "CANCEL":
        cancel_handler(bot, update)
    elif identifier == "EDITMONEY":
        money.edit_money(bot, update)


def cancel_handler(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
    update.callback_query.message.delete()

    bot.send_message(chat_id=chat_id, text="Operazione annullata.")


def create_callback_data(*arg):
    """ Create the callback data associated to each button"""
    return ";".join(unicode(i) for i in arg)


def separate_callback_data(data):
    """ Separate the callback data"""
    return [unicode(i) for i in data.split(";")]
