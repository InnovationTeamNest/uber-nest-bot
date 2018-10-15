# -*- coding: utf-8 -*-
import sys

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import create_callback_data as ccd, separate_callback_data
from util.keyboards import me_keyboard, trips_keyboard


# Informazioni sulla notazione usata (limitazione delle API a 64 byte per chiamata)
#
# TRIPS -> entrypoint per action_trips.py
# DRIVER -> rimozione o aggiunta del driver
# US_RE = USER_REMOVAL
# ED_DR_SL = EDIT_DRIVER_SLOTS
# CO_DR = CONFIRM_DRIVER
# CO_DR_RE = CONFIRM_DRIVER_REMOVAL
# CO_US_RE = CONFIRM_USER_REMOVAL


def me(bot, update):
    if update.callback_query:
        chat_id = update.callback_query.from_user.id
        try:
            update.callback_query.message.delete()
        except BadRequest:
            print("Failed to delete previous message", file=sys.stderr)
    else:
        chat_id = update.message.chat_id

    if str(chat_id) in secret_data.users:
        bot.send_message(chat_id=chat_id, text="Cosa vuoi fare?", reply_markup=me_keyboard(chat_id))


def me_handler(bot, update):
    action = separate_callback_data(update.callback_query.data)[1]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        print("Failed to delete previous message", file=sys.stderr)

    if action == "TRIPS":  # Visualizza i vari trips dell'utente
        bot.send_message(chat_id=chat_id,
                         text="Viaggi (clicca su un viaggio per modificarlo):",
                         reply_markup=trips_keyboard(str(chat_id)))
    elif action == "DRIVER":  # Aggiunta o rimozione della modalità guidatore
        if str(chat_id) in secret_data.drivers:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=ccd("ME", "CO_DR_RE")),
                 InlineKeyboardButton("No", callback_data=ccd("ME_MENU"))]]
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler confermare la tua rimozione dalla"
                                  " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                  " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                  " completo di tutti i viaggi, impostazioni e crediti.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=ccd("ME", "ED_DR_SL")),
                 InlineKeyboardButton("No", callback_data=ccd("ME_MENU"))]]
            bot.send_message(chat_id=chat_id,
                             text="Una volta finalizzata l'iscrizione come autista, potrai gestire i tuoi"
                                  " viaggi direttamente da questo bot. Contatta un membro del direttivo di"
                                  " UberNEST per ulteriori informazioni.\n\n"
                                  "Sei sicuro di voler diventare un autista di UberNEST?",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "US_RE":
        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("ME", "CO_US_RE")),
             InlineKeyboardButton("No", callback_data=ccd("ME_MENU"))]]

        user_debits = secret_data.users[str(chat_id)]["Debit"]
        debitors = ""
        for creditor in user_debits:
            debitors += secret_data.users[creditor]["Name"] + " - " + str(user_debits[creditor]) + " EUR"

        message_text = "Sei sicuro di voler confermare la tua rimozione completa dal sistema?" \
                       + " L'operazione è reversibile, ma tutte le" \
                       + " tue prenotazioni e viaggi verranno cancellati per sempre."

        if debitors != "":
            message_text += "\n\nATTENZIONE! Hai debiti con le seguenti persone," \
                            " in caso di cancellazione dal sistema" \
                            " verranno avvisate dei tuoi debiti non saldati!\n" + debitors

        bot.send_message(chat_id=chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "ED_DR_SL":
        # Inserisco 5 bottoni per i posti con la list comprehension
        keyboard = [[InlineKeyboardButton(str(i), callback_data=ccd("ME", "CO_DR", str(i)))
                     for i in range(1, 6, 1)],
                    [InlineKeyboardButton("Indietro", callback_data=ccd("ME_MENU"))],
                    [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]]
        bot.send_message(chat_id=chat_id,
                         text="Inserisci il numero di posti disponibili nella tua macchina, autista escluso.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "CO_DR":
        slots = int(separate_callback_data(update.callback_query.data)[2])
        if str(chat_id) in secret_data.drivers:
            bot.send_message(chat_id=chat_id,
                             text="Numero di posti della vettura aggiornato con successo.")
        else:
            secret_data.drivers[str(chat_id)] = {"Slots": slots}
            bot.send_message(chat_id=chat_id,
                             text="Sei stato inserito nella lista degli autisti! Usa il menu /me per aggiungere"
                                  " viaggi, modificare i posti auto, aggiungere un messaggio da mostrare ai tuoi"
                                  " passeggeri ed altro.")
    elif action == "CO_DR_RE":
        common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id,
                         text="Sei stato rimosso con successo dall'elenco degli autisti.")
    elif action == "CO_US_RE":
        user_debits = secret_data.users[str(chat_id)]["Debit"]
        for creditor in user_debits:
            bot.send_message(chat_id=creditor,
                             text="ATTENZIONE! " + secret_data.users[str(chat_id)]["Name"]
                                  + " si è cancellato da UberNEST. Ha ancora "
                                  + str(user_debits[creditor]) + " EUR di debito con te.")

        del secret_data.users[str(chat_id)]
        if str(chat_id) in secret_data.drivers:
            common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id, text="Sei stato rimosso con successo dal sistema.")


def newtrip_handler(bot, update):
    data = separate_callback_data(update.callback_query.data)[1:]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        print("Failed to delete previous message", file=sys.stderr)

    # NOTA BENE: (Python 2.7 non supporta argomenti di posizione dopo *)
    if len(data) == 1:  # Inserimento del giorno
        keyboard = []

        for day in common.work_days:  # Ordine: giorno, direzione
            keyboard.append(InlineKeyboardButton(day[:2], callback_data=ccd("NEWTRIP", day, *data)))

        keyboard = [keyboard,
                    [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS"))],
                    [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]]

        bot.send_message(chat_id=chat_id, text="Scegli il giorno della settimana del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 2:  # Inserimento dell'ora
        # Ordine: ora, giorno, direzione
        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(14, 21, 1)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("NEWTRIP", *data[1:]))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio. ",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 3:  # Inserimento dei minuti
        # Ordine: minuti, ora, giorno, direzione
        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(30, 60, 5)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("NEWTRIP", *data[1:]))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Scegli i minuti di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 4:  # Conferma finale data all'utente
        minute, hour, day, direction = data
        time = hour.zfill(2) + ":" + minute.zfill(2)

        secret_data.groups[direction][str(day)][str(chat_id)] = {"Time": str(time),
                                                                         "Permanent": [],
                                                                         "Temporary": [],
                                                                         "SuspendedUsers": [],
                                                                         "Suspended": False}

        message_text = "Viaggio aggiunto con successo:" \
                       + "\n\n➡: " + common.direction_to_name(direction) \
                       + "\n🗓: " + day \
                       + "\n🕓: " + str(time)

        bot.send_message(chat_id=chat_id, text=message_text)
    else:
        bot.send_message(chat_id=chat_id, text="Spiacente, si è verificato un errore. Riprova più tardi.")
