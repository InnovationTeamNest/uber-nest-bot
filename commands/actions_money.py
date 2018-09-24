# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from services import money as mn
from util import common, filters


def check_money(bot, update):
    chat_id = update.callback_query.from_user.id

    debits = mn.get_debits(str(chat_id))
    if len(debits) != 0:
        string = ""
        for creditor in debits:
            string += secret_data.users[str(creditor[0])]["Name"] + " - " + str(creditor[1]) + " EUR\n"
        message = "Al momento possiedi debiti verso le seguenti persone: \n" + string \
                  + "\nContattali per saldare i debiti."
    else:
        message = "Al momento sei a posto con i debiti."

    if str(chat_id) in secret_data.drivers:
        credits = mn.get_credits(str(chat_id))
        if len(credits) > 0:
            keyboard = []
            for debitor in credits:
                keyboard.append([InlineKeyboardButton(
                    secret_data.users[str(debitor[0])]["Name"] + " - " + str(debitor[1]) + " EUR",
                    callback_data=filters.create_callback_data("EDITMONEY", "NONE", *debitor))])
            keyboard.append(
                [InlineKeyboardButton("Esci", callback_data=filters.create_callback_data("CANCEL"))])
            bot.send_message(chat_id=chat_id,
                             text=message + "\n\nAl momento possiedi queste persone hanno debiti con te. Clicca "
                                            "su uno per modificarne o azzerarne il debito:",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text=message + "\n\nNessuno ti deve denaro al momento.")
    else:
        bot.send_message(chat_id=chat_id, text=message)


def edit_money(bot, update):
    action, user, money = filters.separate_callback_data(update.callback_query.data)[1:]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    if action == "SUBTRACT":
        secret_data.users[user]["Debit"][str(chat_id)] -= common.trip_price
        money = str(float(money) - common.trip_price)
    elif action == "ZERO":
        money = "0"

    message = secret_data.users[user]["Name"] + ": " + money + " EUR"

    keyboard = []

    if float(money) > 0:
        keyboard.append(InlineKeyboardButton("-" + str(common.trip_price) + " EUR",
                                             callback_data=filters.create_callback_data(
                                                 "EDITMONEY", "SUBTRACT", user, money)))
        keyboard.append(InlineKeyboardButton("Azzera",
                                             callback_data=filters.create_callback_data("EDITMONEY", "ZERO", user, 0)))
    else:
        del secret_data.users[user]["Debit"][str(chat_id)]

    keyboard.append(InlineKeyboardButton("Indietro", callback_data=filters.create_callback_data("ME", "MONEY")))

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
