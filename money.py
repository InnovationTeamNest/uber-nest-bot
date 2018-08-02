# -*- coding: utf-8 -*-

import datetime
import common
import inline
import secrets

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup


def process_debits():  # Questo comando verrà fatto partire alle 02:00 di ogni giorno
    today = datetime.datetime.today().weekday()
    if 1 <= today <= 5:
        for direction in secrets.groups:
            trips = secrets.groups[direction][common.day_to_string(today - 1)]
            for driver in trips:
                for mode in trips[driver]:
                    if mode != u"Time":
                        for user in trips[driver][mode]:
                            try:
                                secrets.users[user][u"Debit"][driver] += secrets.trip_price
                            except KeyError:
                                secrets.users[user][u"Debit"][driver] = secrets.trip_price
                trips[driver][u"Temporary"] = {}


def edit_money(bot, update):
    action, user, money = inline.separate_callback_data(update.callback_query.data)[1:]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if action == "SUBTRACT":
        secrets.users[user][u"Debit"][str(chat_id)] -= secrets.trip_price
        money = str(float(money) - secrets.trip_price)
        message = secrets.users[user][u"Name"] + ": " + money + " EUR"
    elif action == "ZERO":
        money = "0"
        message = secrets.users[user][u"Name"] + ": 0 EUR"
    else:
        message = secrets.users[user][u"Name"] + ": " + money + " EUR"

    keyboard = []

    if float(money) > 0:
        keyboard.append(InlineKeyboardButton("-" + str(secrets.trip_price) + " EUR",
                                             callback_data=inline.create_callback_data(
                                                 "EDITMONEY", "SUBTRACT", user, money)))
        keyboard.append(InlineKeyboardButton("Azzera",
                                             callback_data=inline.create_callback_data(
                                                 "EDITMONEY", "ZERO", user, 0)))
    else:
        del secrets.users[user][u"Debit"][str(chat_id)]

    keyboard.append(InlineKeyboardButton("Indietro", callback_data=inline.create_callback_data("ME", "MONEY")))

    bot.send_message(chat_id=chat_id, text=message, reply_markup=InlineKeyboardMarkup([keyboard]))


def get_credits(input_creditor):
    return [(user, secrets.users[user][u"Debit"][creditor]) for user in secrets.users
            for creditor in secrets.users[user][u"Debit"] if creditor == input_creditor]


def get_debits(input_debitor):
    return [(creditor, secrets.users[input_debitor][u"Debit"][creditor])
            for creditor in secrets.users[input_debitor][u"Debit"]]
