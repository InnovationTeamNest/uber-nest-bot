# -*- coding: utf-8 -*-
import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secrets
import util.common
from util import common
from util.common import PAGE_SIZE
from util.filters import create_callback_data as ccd, separate_callback_data


def check_money(bot, update):
    chat_id = str(update.callback_query.message.chat_id)

    keyboard = [
        [InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))],
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    message = []

    # Prima raccolgo sottoforma di stringa i debiti (per tutti gli utenti)
    debit_list = util.common.get_debits(chat_id)

    if len(debit_list) > 0:
        people = []
        for creditor_id, value in debit_list:
            people.append(f"[{secrets.users[creditor_id]['Name']}](tg://user?id={creditor_id})"
                          f" 💶 {str(value)} EUR\n")

        message.append(f"💸 Al momento possiedi debiti verso le seguenti persone:\n{''.join(people)}"
                       f"\nContatta ciascun autista per saldare i relativi debiti.")
    else:
        message.append("💰 Al momento sei a posto con i debiti.")

    # Poi creo un bottone separato per ogni credito.
    # Questa sezione del codice viene fatta girare solo se l'utente è un autista.
    if chat_id in secrets.drivers:
        keyboard.insert(0, [InlineKeyboardButton("➕ Aggiungi un nuovo debitore", callback_data=ccd("NEW_DEBITOR", 0))])

        credit_list = util.common.get_credits(chat_id)
        if len(credit_list) > 0:
            for debitor_id, value in credit_list:
                keyboard.insert(0, [InlineKeyboardButton(f"{secrets.users[debitor_id]['Name']} 💶 {str(value)} EUR",
                                                         callback_data=ccd("EDIT_MONEY", "VIEW", debitor_id))])

            message.append("\n\n💰 Al momento possiedi queste persone hanno debiti con te. "
                           "Clicca su una persona per modificare o azzerare il debito:")
        else:
            message.append("\n\n💸 Nessuno ti deve denaro al momento.")

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          parse_mode="Markdown",
                          text="".join(message),
                          reply_markup=InlineKeyboardMarkup(keyboard))


def edit_money(bot, update):
    action, user = separate_callback_data(update.callback_query.data)[1:]
    chat_id = str(update.callback_query.message.chat_id)

    try:
        money = str(secrets.users[user]["Debit"][chat_id])
    except KeyError:
        secrets.users[user]["Debit"][chat_id] = 0
        money = "0.0"

    #
    # Tre azioni possibili: SUBTRACT (sottrae il prezzo di un viaggio), ADD (aggiunge il prezzo
    # di un viaggio), ZERO (cancella completamente il debito)
    #

    if action == "SUBTRACT":
        secrets.users[user]["Debit"][chat_id] -= common.trip_price
        money = str(float(money) - common.trip_price)

        user_text = f"💶 Hai saldato {str(common.trip_price)} EUR con " \
                    f"[{secrets.users[chat_id]['Name']}](tg://user?id={chat_id}). " \
                    f"Debito corrente : {money} EUR."

    elif action == "ADD":
        secrets.users[user]["Debit"][chat_id] += common.trip_price
        money = str(float(money) + common.trip_price)
        user_text = f"💶 [{secrets.users[chat_id]['Name']}](tg://user?id={chat_id})" \
                    f" ti ha addebitato {str(common.trip_price)} EUR. " \
                    f"Debito corrente: {money} EUR."

    elif action == "ZERO":
        del secrets.users[user]["Debit"][chat_id]
        money = "0.0"
        user_text = f"💸 [{secrets.users[chat_id]['Name']}](tg://user?id={chat_id})" \
                    f" ha azzerato il debito con te."

    else: # Caso in cui l'azione è VIEW
        user_text = ""

    keyboard = [
        [
            InlineKeyboardButton(f"+ {str(common.trip_price)} EUR",
                                 callback_data=ccd("EDIT_MONEY", "ADD", user)),
            InlineKeyboardButton(f"- {str(common.trip_price)} EUR",
                                 callback_data=ccd("EDIT_MONEY", "SUBTRACT", user)),
            InlineKeyboardButton("Azzera",
                                 callback_data=ccd("EDIT_MONEY", "ZERO", user))
        ],
        [InlineKeyboardButton("↩ Indietro", callback_data=ccd("MONEY"))],
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text=f"👤 [{secrets.users[user]['Name']}](tg://user?id={user})"
                               f"\n💶 *{money} EUR*", reply_markup=InlineKeyboardMarkup(keyboard),
                          parse_mode="Markdown")

    if not action == "VIEW":
        bot.send_message(chat_id=user, text=user_text,
                         parse_mode="Markdown")


def new_debitor(bot, update):
    """
    Questo metodo lista tutti gli utenti del sistema, selezionabili per aggiungere un nuovo debito.

    I potenziali passeggeri vengono listati su più pagine per evitare messaggi infiniti. A ogni pagina è
    associata un bottone che permette di aprirla immediatamente. In ogni pagina vi sono PAGE_SIZE persone,
    costante definita in util/common.py.

    Una volta selezionato un utente, viene aperto edit_money(bot, update) con il debito automaticamente
    settato a zero.
    """
    chat_id = str(update.callback_query.message.chat_id)
    page = int(separate_callback_data(update.callback_query.data)[1])

    keyboard = []
    users = sorted(  # Resituisce una lista di tuple del tipo (Nome, ID)
        [(secrets.users[user]["Name"], user)
         for user in secrets.users
         if user != chat_id and chat_id not in secrets.users[user]["Debit"]]
    )

    for index in range(PAGE_SIZE * page, PAGE_SIZE * (page + 1), 1):
        try:
            name, name_chat_id = users[index]
            keyboard.append([InlineKeyboardButton(name, callback_data=ccd("EDIT_MONEY", "VIEW", name_chat_id))])
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
    keyboard.append([InlineKeyboardButton("↩ Indietro", callback_data=ccd("MONEY"))])
    keyboard.append([InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))])

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text="Scegli un utente a cui aggiungere un debito.",
                          reply_markup=InlineKeyboardMarkup(keyboard))
