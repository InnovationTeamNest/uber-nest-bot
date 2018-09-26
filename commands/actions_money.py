# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from services import money as mn
from util import common
from util.filters import create_callback_data as ccd, separate_callback_data


def check_money(bot, update):
    chat_id = str(update.callback_query.from_user.id)
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    # Prima raccolgo sottoforma di stringa i debiti
    debits = mn.get_debits(chat_id)
    if len(debits) != 0:
        string = ""
        for creditor in debits:
            string += secret_data.users[str(creditor[0])]["Name"] + " - " + str(creditor[1]) + " EUR\n"
        message = "Al momento possiedi debiti verso le seguenti persone: \n" \
                  + string + "\nContattali per saldare i debiti."
    else:
        message = "Al momento sei a posto con i debiti."

    # Poi creo un bottone separato per ogni credito
    if chat_id in secret_data.drivers:
        keyboard = [
            [InlineKeyboardButton("Aggiungi un nuovo debitore", callback_data=ccd("NEW_DEBITOR"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME_MENU"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        credits = mn.get_credits(chat_id)
        if len(credits) > 0:
            for debitor in credits:
                name, value = debitor
                keyboard.insert(0, [InlineKeyboardButton(secret_data.users[name]["Name"] + " - " + str(value) + " EUR",
                                                         callback_data=ccd("EDIT_MONEY", "NONE", *debitor))])
            bot.send_message(chat_id=chat_id,
                             text=message + "\n\nAl momento possiedi queste persone hanno debiti con te. Clicca "
                                            "su uno per modificarne il debito:",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id,
                             text=message + "\n\nNessuno ti deve denaro al momento.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id=chat_id, text=message)


def edit_money(bot, update):
    action, user, money = separate_callback_data(update.callback_query.data)[1:]
    chat_id = str(update.callback_query.from_user.id)
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    if action == "SUBTRACT":
        try:
            secret_data.users[user]["Debit"][chat_id] -= common.trip_price
        except KeyError:
            secret_data.users[user]["Debit"][chat_id] = -common.trip_price

        money = str(float(money) - common.trip_price)

        bot.send_message(chat_id=user,
                         text="Hai saldato " + str(common.trip_price)
                              + " EUR con " + secret_data.users[chat_id]["Name"]
                              + ". Debito corrente :" + money + " EUR.")
    elif action == "ADD":
        try:
            secret_data.users[user]["Debit"][chat_id] += common.trip_price
        except KeyError:
            secret_data.users[user]["Debit"][chat_id] = common.trip_price

        money = str(float(money) + common.trip_price)

        bot.send_message(chat_id=user,
                         text=secret_data.users[chat_id]["Name"]
                              + " ti ha addebitato " + str(common.trip_price) + " EUR con "
                              + ". Debito corrente: " + money + " EUR.")

    elif action == "ZERO":
        money = "0"
        bot.send_message(chat_id=user,
                         text=secret_data.users[chat_id]["Name"] + " ha azzerato il debito con te.")

    message = secret_data.users[user]["Name"] + ": " + money + " EUR"

    keyboard = [InlineKeyboardButton("+" + str(common.trip_price) + " EUR",
                                     callback_data=ccd("EDIT_MONEY", "ADD", user, money))]

    if float(money) > 0:
        keyboard.append(InlineKeyboardButton("-" + str(common.trip_price) + " EUR",
                                             callback_data=ccd("EDIT_MONEY", "SUBTRACT", user, money)))
        keyboard.append(InlineKeyboardButton("Azzera",
                                             callback_data=ccd("EDIT_MONEY", "ZERO", user, 0)))
    else:
        try:
            del secret_data.users[user]["Debit"][chat_id]
        except KeyError:
            log.info("No debit found for " + str(user) + " with " + str(chat_id))

    keyboard = [
        keyboard,
        [InlineKeyboardButton("Indietro", callback_data=ccd("MONEY"))],
        [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
    ]

    bot.send_message(chat_id=chat_id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))


def new_debitor(bot, update):
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    keyboard = []
    for user in secret_data.users:
        if not secret_data.users[user]["Debit"] and user != chat_id:
            keyboard.append([InlineKeyboardButton(secret_data.users[user]["Name"],
                                                  callback_data=ccd("EDIT_MONEY", "NONE", user, "0.0"))])

    keyboard.append([InlineKeyboardButton("Indietro", callback_data=ccd("MONEY"))])
    keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])

    bot.send_message(chat_id=chat_id,
                     text="Scegli un utente a cui aggiungere un debito.",
                     reply_markup=InlineKeyboardMarkup(keyboard))


def edit_money_admin(bot, update, args):
    if str(update.message.chat_id) == secret_data.owner_id:
        try:
            debitor, creditor, value = args
            secret_data.users[str(debitor)]["Debit"][str(creditor)] = float(value)
            bot.send_message(chat_id=secret_data.owner_id,
                             text="Modifica in corso: "
                                  + "\n\nDebitore: " + secret_data.users[str(debitor)]["Name"]
                                  + "\nCreditore: " + secret_data.users[str(creditor)]["Name"]
                                  + "\nDebito inserito: " + str(value))
        except Exception:
            bot.send_message(chat_id=secret_data.owner_id, text="Sintassi non corretta. Riprova!")
