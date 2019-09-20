# -*- coding: utf-8 -*-
import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from data.data_api import (get_name, is_driver, set_single_debit, get_single_debit,
                           remove_single_debit, get_debit_tuple, get_credits, get_new_debitors, quick_debit_edit)
from routing.filters import create_callback_data as ccd, separate_callback_data
from util import common
from util.common import PAGE_SIZE


def check_money(bot, update):
    chat_id = str(update.callback_query.message.chat_id)

    keyboard = [
        [InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))],
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    message = []

    # Prima raccolgo sottoforma di stringa i debiti (per tutti gli utenti)
    debit_list = get_debit_tuple(chat_id)

    if len(debit_list) > 0:
        people = []
        for creditor_id, value in debit_list:
            people.append(f"[{get_name(creditor_id)}](tg://user?id={creditor_id})"
                          f" 🚗 {str(value)} {'viaggi' if value > 1 else 'viaggio'}\n")

        message.append(f"💸 Al momento risultano viaggi da pagare alle seguenti persone:\n{''.join(people)}"
                       f"\nContatta ciascun autista per saldare i relativi debiti.")
    else:
        message.append("💰 Al momento non hai viaggi non saldati.")

    # Poi creo un bottone separato per ogni credito.
    # Questa sezione del codice viene fatta girare solo se l'utente è un autista.
    if is_driver(chat_id):
        keyboard.insert(0, [InlineKeyboardButton("➕ Aggiungi un nuovo debitore", callback_data=ccd("NEW_DEBITOR", 0))])

        credit_list = get_credits(chat_id)
        if len(credit_list) > 0:
            for debitor_id, value in credit_list:
                keyboard.insert(0, [InlineKeyboardButton(f"{get_name(debitor_id)} 🚗 {str(value)} {'viaggi' if value > 1 else 'viaggio'}",
                                                         callback_data=ccd("EDIT_MONEY", "VIEW", debitor_id))])

            message.append("\n\n💰 Al momento possiedi queste persone hanno viaggi non saldati con te. "
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
        trips = str(get_single_debit(user, chat_id))
    except KeyError:
        set_single_debit(user, chat_id, 0)
        trips = "0"

    #
    # Tre azioni possibili: SUBTRACT (sottrae il prezzo di un viaggio), ADD (aggiunge il prezzo
    # di un viaggio), ZERO (cancella completamente il debito)
    #

    edit_money_keyboard = [
        InlineKeyboardButton(f"+",
                             callback_data=ccd("EDIT_MONEY", "ADD", user)),
        InlineKeyboardButton(f"-",
                             callback_data=ccd("EDIT_MONEY", "SUBTRACT", user))
    ]

    if action == "SUBTRACT":
        trips = quick_debit_edit(user, chat_id, "-")

        user_text = f"💶 Hai saldato un viaggio con " \
            f"[{get_name(chat_id)}](tg://user?id={chat_id}). " \
            f"Viaggi da pagare rimanenti: {trips}."

    elif action == "ADD":
        trips = quick_debit_edit(user, chat_id, "+")
        user_text = f"💶 [{get_name(chat_id)}](tg://user?id={chat_id})" \
            f" ha aggiunto un viaggio da pagargli.\n" \
            f"Viaggi da pagare rimanenti: {trips}."

    elif action == "ZERO":
        remove_single_debit(user, chat_id)
        trips = 0
        user_text = f"💸 [{get_name(chat_id)}](tg://user?id={chat_id})" \
            f" ha azzerato i viaggi da pagare con te."

    elif action == "NEW":
        trips = 0
        user_text = ""

    elif action == "VIEW":
        user_text = ""

    else:
        user_text = "Sembra che questo messaggio sia stato mandato inavvertitamente.\n" \
                    "Contatta il creatore del bot per segnalare il problema."

    if trips != 0:
        edit_money_keyboard.append(InlineKeyboardButton("Azzera", callback_data=ccd("EDIT_MONEY", "ZERO", user)))

    keyboard = [
        edit_money_keyboard,
        [InlineKeyboardButton("↩ Indietro", callback_data=ccd("MONEY"))],
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text=f"👤 [{get_name(user)}](tg://user?id={user})"
                          f"\n🚗 *{trips} {'viaggi' if trips > 1 else 'viaggio'}*",
                          reply_markup=InlineKeyboardMarkup(keyboard),
                          parse_mode="Markdown")

    if action == "ADD" or action == "ZERO" or action == "SUBTRACT":
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
    users = get_new_debitors(chat_id)

    for index in range(PAGE_SIZE * page, PAGE_SIZE * (page + 1), 1):
        try:
            name, name_chat_id = users[index]
            keyboard.append([InlineKeyboardButton(name, callback_data=ccd("EDIT_MONEY", "NEW", name_chat_id))])
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
                          text="Scegli un utente a cui aggiungere un viaggio da pagare.",
                          reply_markup=InlineKeyboardMarkup(keyboard))
