# -*- coding: utf-8 -*-

from actions_booking import booking_handler
from actions_me import me_handler


def inline_handler(bot, update):
    identifier = separate_callback_data(update.callback_query.data)[0]
    if identifier == "BOOKING":
        booking_handler(bot, update)
    elif identifier == "ME":
        me_handler(bot, update)


def create_callback_data(identifier, args):
    """ Create the callback data associated to each button"""
    args.insert(0, identifier)
    return ";".join(str(i) for i in args)


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")
