# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging as log

import webapp2
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, Bot

import common
import dumpable
import inline
import secret_data

bot = Bot(secret_data.bot_token)


class MoneyHandler(webapp2.RequestHandler):
    def get(self):
        dumpable.get_data()
        process_debits()
        dumpable.dump_data()
        self.response.write("See console for output.")


def process_debits():
    """Questo comando verrà fatto partire alle 02:00 di ogni giorno"""
    today = datetime.datetime.today()
    if 1 <= today.weekday() <= 5 and today.date() not in common.no_trip_days:
        for direction in secret_data.groups:
            trips = secret_data.groups[direction][common.day_to_string(today.weekday() - 1)]
            for driver in trips:
                for mode in trips[driver]:
                    if mode == "Temporary" or mode == "Permanent":
                        for user in trips[driver][mode]:
                            try:
                                secret_data.users[user]["Debit"][driver] += common.trip_price
                            except KeyError:
                                secret_data.users[user]["Debit"][driver] = common.trip_price
                            bot.send_message(chat_id=str(user),
                                             text="Ti sono stati addebitati " + str(common.trip_price)
                                                  + " EUR da " + str(secret_data.users[driver]["Name"]))
                            bot.send_message(chat_id=str(driver),
                                             text="Hai ora un credito di " + str(common.trip_price)
                                                  + " EUR da parte di " + str(secret_data.users[user]["Name"]))
                            log.debug(user + "'s debit from "
                                      + driver + " = " + str(secret_data.users[user]["Debit"][driver]))
                trips[driver]["Temporary"] = []


def edit_money(bot, update):
    action, user, money = inline.separate_callback_data(update.callback_query.data)[1:]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if action == "SUBTRACT":
        secret_data.users[user]["Debit"][str(chat_id)] -= common.trip_price
        money = str(float(money) - common.trip_price)
    elif action == "ZERO":
        money = "0"

    message = secret_data.users[user]["Name"] + ": " + money + " EUR"

    keyboard = []

    if float(money) > 0:
        keyboard.append(InlineKeyboardButton("-" + str(common.trip_price) + " EUR",
                                             callback_data=inline.create_callback_data(
                                                 "EDITMONEY", "SUBTRACT", user, money)))
        keyboard.append(InlineKeyboardButton("Azzera",
                                             callback_data=inline.create_callback_data("EDITMONEY", "ZERO", user, 0)))
    else:
        del secret_data.users[user]["Debit"][str(chat_id)]

    keyboard.append(InlineKeyboardButton("Indietro", callback_data=inline.create_callback_data("ME", "MONEY")))

    bot.send_message(chat_id=chat_id, text=message, reply_markup=InlineKeyboardMarkup([keyboard]))


def edit_money_admin(bot, update, args):
    if str(update.message.chat_id) == secret_data.owner_id:
        try:
            debitor, creditor, value = args
            secret_data.users[str(debitor)]["Debit"][str(creditor)] = value
            bot.send_message(chat_id=secret_data.owner_id,
                             text="Modifica in corso: "
                                  + "\n\nDebitore: " + secret_data.users[str(debitor)]["Name"]
                                  + "\nCreditore: " + secret_data.users[str(creditor)]["Name"]
                                  + "\nDebito inserito: " + str(value))
        except Exception:
            bot.send_message(chat_id=secret_data.owner_id, text="Sintassi non corretta. Riprova!")


def get_credits(input_creditor):
    return [(user, secret_data.users[user]["Debit"][creditor]) for user in secret_data.users
            for creditor in secret_data.users[user]["Debit"] if creditor == input_creditor]


def get_debits(input_debitor):
    return [(creditor, secret_data.users[input_debitor]["Debit"][creditor])
            for creditor in secret_data.users[input_debitor]["Debit"]]
