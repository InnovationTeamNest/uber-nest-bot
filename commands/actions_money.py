# -*- coding: utf-8 -*-
import math
import sys

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
import util.common
from util import common
from util.common import PAGE_SIZE
from util.filters import create_callback_data as ccd, separate_callback_data


def check_money(bot, update):
    chat_id = str(update.callback_query.from_user.id)
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        update.callback_query.message.delete()
    except BadRequest:
        print("Failed to delete previous message", file=sys.stderr)

    # Prima raccolgo sottoforma di stringa i debiti
    debits = util.common.get_debits(chat_id)

    if len(debits) != 0:
        string = ""
        for name, value in debits:
            string += secret_data.users[name]["Name"] + " - " + str(value) + " EUR\n"

        message = "Al momento possiedi debiti verso le seguenti persone: \n" \
                  + string + "\nContattali per saldare i debiti."
    else:
        message = "Al momento sei a posto con i debiti."

    # Poi creo un bottone separato per ogni credito
    if chat_id in secret_data.drivers:
        keyboard = [
            [InlineKeyboardButton("Aggiungi un nuovo debitore", callback_data=ccd("NEW_DEBITOR", 0))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME_MENU"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        credits = util.common.get_credits(chat_id)
        if len(credits) > 0:
            for name, value in credits:
                keyboard.insert(0, [InlineKeyboardButton(secret_data.users[name]["Name"] + " - " + str(value) + " EUR",
                                                         callback_data=ccd("EDIT_MONEY", "VIEW", name))])
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
    action, user = separate_callback_data(update.callback_query.data)[1:]
    chat_id = str(update.callback_query.from_user.id)
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        money = str(secret_data.users[user]["Debit"][chat_id])
    except KeyError:
        secret_data.users[user]["Debit"][chat_id] = 0
        money = "0.0"

    try:
        update.callback_query.message.delete()
    except BadRequest:
        print("Failed to delete previous message", file=sys.stderr)

    #
    # Tre azioni possibili: SUBTRACT (sottrae il prezzo di un viaggio), ADD (aggiunge il prezzo
    # di un viaggio), ZERO (cancella completamente il debito)
    #
    if action == "SUBTRACT":
        secret_data.users[user]["Debit"][chat_id] -= common.trip_price
        money = str(float(money) - common.trip_price)
        user_text = "Hai saldato " + str(common.trip_price) \
                    + " EUR con " + secret_data.users[chat_id]["Name"] \
                    + ". Debito corrente :" + money + " EUR."

    elif action == "ADD":
        secret_data.users[user]["Debit"][chat_id] += common.trip_price
        money = str(float(money) + common.trip_price)
        user_text = secret_data.users[chat_id]["Name"] \
                    + " ti ha addebitato " + str(common.trip_price) + " EUR con " \
                    + ". Debito corrente: " + money + " EUR."

    elif action == "ZERO":
        del secret_data.users[user]["Debit"][chat_id]
        money = "0.0"
        user_text = secret_data.users[chat_id]["Name"] + " ha azzerato il debito con te."

    else:
        user_text = ""

    keyboard = [
        [
            InlineKeyboardButton("+" + str(common.trip_price) + " EUR",
                                 callback_data=ccd("EDIT_MONEY", "ADD", user)),
            InlineKeyboardButton("-" + str(common.trip_price) + " EUR",
                                 callback_data=ccd("EDIT_MONEY", "SUBTRACT", user)),
            InlineKeyboardButton("Azzera",
                                 callback_data=ccd("EDIT_MONEY", "ZERO", user))
        ],
        [InlineKeyboardButton("Indietro", callback_data=ccd("MONEY"))],
        [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
    ]

    bot.send_message(chat_id=chat_id, text=secret_data.users[user]["Name"] + ": " + money + " EUR",
                     reply_markup=InlineKeyboardMarkup(keyboard))

    if not action == "VIEW":
        bot.send_message(chat_id=user, text=user_text)


def new_debitor(bot, update):
    """
    Questo metodo lista tutti gli utenti del sistema, selezionabili per aggiungere un nuovo debito.

    I potenziali passeggeri vengono listati su più pagine per evitare messaggi infiniti. A ogni pagina è
    associata un bottone che permette di aprirla immediatamente. In ogni pagina vi sono PAGE_SIZE persone,
    costante definita in util/common.py.

    Una volta selezionato un utente, viene aperto edit_money(bot, update) con il debito automaticamente
    settato a zero.
    """
    chat_id = str(update.callback_query.from_user.id)
    page = int(separate_callback_data(update.callback_query.data)[1])

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        update.callback_query.message.delete()
    except BadRequest:
        print("Failed to delete previous message", file=sys.stderr)

    keyboard = []
    users = sorted(  # Resituisce una lista di tuple del tipo (Nome, ID)
        [(secret_data.users[user]["Name"], user)
         for user in secret_data.users
         if user != chat_id and chat_id not in secret_data.users[user]["Debit"]]
    )

    for index in range(PAGE_SIZE * page, PAGE_SIZE * (page + 1), 1):
        try:
            name, id = users[index]
            keyboard.append(
                [InlineKeyboardButton(name, callback_data=ccd("EDIT_MONEY", "VIEW", id))]
            )
        except IndexError:
            break

    # Aggiungo un bottone per ogni pagina, in quanto la lista è troppo grande
    page_buttons = []
    for index in range(0, int(math.ceil(len(users) / PAGE_SIZE)), 1):
        if index == page:
            text = "☑"
        else:
            text = str(index + 1)

        page_buttons.append(InlineKeyboardButton(text, callback_data=ccd("NEW_DEBITOR", index)))

    keyboard.append(page_buttons)
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
