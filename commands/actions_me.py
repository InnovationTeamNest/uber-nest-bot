# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import logging as log

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import create_callback_data, separate_callback_data
from util.keyboards import me_keyboard, trips_keyboard


def me(bot, update):
    if str(update.message.chat_id) in secret_data.users:
        bot.send_message(chat_id=update.message.chat_id, text="Cosa vuoi fare?", reply_markup=me_keyboard(update))


def me_handler(bot, update):
    mode = separate_callback_data(update.callback_query.data)[1]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    log.debug("Mode entered: " + mode)

    if mode == "TRIPS":
        # Visualizza i vari trips dell'utente
        bot.send_message(chat_id=chat_id,
                         text="Viaggi (clicca su un viaggio per rimuoverlo):",
                         reply_markup=trips_keyboard(update))
    elif mode == "DRIVER":
        if str(chat_id) in secret_data.drivers:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=create_callback_data("ME", "DELETEDRIVER")),
                 InlineKeyboardButton("No", callback_data=create_callback_data("CANCEL"))]]
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler confermare la tua rimozione dalla"
                                  " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                  " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                  " completo di tutte le prenotazioni.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=create_callback_data("ME", "SLOTSDRIVER")),
                 InlineKeyboardButton("No", callback_data=create_callback_data("CANCEL"))]]
            bot.send_message(chat_id=chat_id,
                             text="Una volta finalizzata l'iscrizione come autista, potrai gestire i tuoi"
                                  " viaggi direttamente da questo bot. Contatta un membro del direttivo di"
                                  " UberNEST per ulteriori informazioni.\n\n"
                                  "Sei sicuro di voler diventare un autista di UberNEST?",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "REMOVAL":
        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=create_callback_data("ME", "CONFIRMREMOVAL")),
             InlineKeyboardButton("No", callback_data=create_callback_data("CANCEL"))]]

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
                            " verranno avvisate dei tuoi debiti non salvati!\n" + debitors

        bot.send_message(chat_id=chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "SLOTSDRIVER":  # Supporto sensato da macchine con 2 posti fino a 5
        keyboard = [InlineKeyboardButton(str(i),
                                         callback_data=create_callback_data("ME", "CONFIRMDRIVER", str(i)))
                    for i in range(1, 6, 1)]  # Inserisco 5 bottoni per i posti con la list comprehension
        bot.send_message(chat_id=chat_id,
                         text="Inserisci il numero di posti disponibili nella tua macchina, autista escluso.",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif mode == "CONFIRMDRIVER":
        slots = int(separate_callback_data(update.callback_query.data)[2])
        if str(chat_id) in secret_data.drivers:
            bot.send_message(chat_id=chat_id,
                             text="Numero di posti della vettura aggiornato con successo.")
        else:
            bot.send_message(chat_id=chat_id,
                             text="Sei stato inserito nella lista degli autisti! Usa il menu /me per aggiungere"
                                  " viaggi, modificare i posti auto, aggiungere un messaggio da mostrare ai tuoi"
                                  " passeggeri ed altro.")
        secret_data.drivers[str(chat_id)] = {"Slots": slots}
    elif mode == "DELETEDRIVER":
        common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id,
                         text="Sei stato rimosso con successo dall'elenco degli autisti.")
    elif mode == "CONFIRMREMOVAL":
        user_debits = secret_data.users[str(chat_id)]["Debit"]
        for creditor in user_debits:
            bot.send_message(chat_id=creditor,
                             message="ATTENZIONE! " + secret_data.users[str(chat_id)]["Name"]
                                     + " si è cancellato da UberNEST. Ha ancora "
                                     + str(user_debits[creditor]) + " EUR di debito con te.")

        del secret_data.users[str(chat_id)]
        if str(chat_id) in secret_data.drivers:
            common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id, text="Sei stato rimosso con successo dal sistema.")


def trips_handler(bot, update):
    mode = separate_callback_data(update.callback_query.data)[1]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    log.debug("Mode entered: " + mode)
    if mode == "ADD":
        keyboard = [
            [InlineKeyboardButton(common.direction_name[0],
                                  callback_data=create_callback_data("NEWTRIP", common.direction_generic[0])),
             InlineKeyboardButton(common.direction_name[1],
                                  callback_data=create_callback_data("NEWTRIP", common.direction_generic[1]))],
            [InlineKeyboardButton("Annulla", callback_data=create_callback_data("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Vuoi aggiungere un viaggio verso il NEST o Povo? Ricorda che puoi aggiungere"
                              " un solo viaggio al giorno per direzione. Eventuali viaggi già presenti"
                              " verranno sovrascritti, passeggeri compresi.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "DELETE":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=create_callback_data("TRIPS", "CONFIRMDELETION",
                                                                           direction, day)),
             InlineKeyboardButton("No", callback_data=create_callback_data("CANCEL"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "CONFIRMDELETION":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]
        del secret_data.groups[direction][day][chat_id]
        bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.")


def newtrip_handler(bot, update):
    data = separate_callback_data(update.callback_query.data)[1:]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    # NOTA BENE: (Python 2.7 non supporta argomenti di posizione dopo *)
    if len(data) == 1:  # Inserimento del giorno
        keyboard = []

        for day in common.work_days:  # Ordine: giorno, direzione
            keyboard.append(InlineKeyboardButton(day[:2],
                                                 callback_data=create_callback_data("NEWTRIP", day, *data)))
        # Aggiungo il pulsante annulla
        keyboard = [keyboard,
                    [InlineKeyboardButton("Annulla", callback_data=create_callback_data("CANCEL"))]]

        bot.send_message(chat_id=chat_id, text="Scegli il giorno della settimana del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 2:  # Inserimento dell'ora
        keyboard = [  # Ordine: ora, giorno, direzione
            [InlineKeyboardButton(str(i).zfill(2),
                                  callback_data=create_callback_data("NEWTRIP", str(i), *data))
             for i in range(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=create_callback_data("NEWTRIP", str(i), *data))
             for i in range(14, 21, 1)],
            [InlineKeyboardButton("Annulla", callback_data=create_callback_data("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio. ",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 3:  # Inserimento dei minuti
        keyboard = [  # Ordine: minuti, ora, giorno, direzione
            [InlineKeyboardButton(str(i).zfill(2), callback_data=create_callback_data("NEWTRIP", str(i), *data))
             for i in range(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=create_callback_data("NEWTRIP", str(i), *data))
             for i in range(30, 60, 5)],
            [InlineKeyboardButton("Annulla", callback_data=create_callback_data("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id, text="Scegli i minuti di partenza del viaggio. ",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 4:  # Conferma finale data all'utente
        minute, hour, day, direction = data
        time = hour.zfill(2) + ":" + minute.zfill(2)

        secret_data.groups[direction][unicode(day)][unicode(chat_id)] = {"Time": str(time),
                                                                         "Permanent": [],
                                                                         "Temporary": []}
        bot.send_message(chat_id=chat_id, text="Viaggio " + common.direction_to_name(direction)
                                               + " aggiunto con successo:" +
                                               "\n\nGiorno: " + day +
                                               "\nOrario: " + str(time))
    else:
        bot.send_message(chat_id=chat_id, text="Spiacente, si è verificato un errore. Riprova più tardi.")


def message_handler(bot, update):
    mode = separate_callback_data(update.callback_query.data)[1]
    chat_id = update.callback_query.from_user.id

    if mode == "EDIT":
        bot.send_message(chat_id=chat_id,
                         text="Inserisci il messaggio che verrà mostrato assieme al viaggio."
                              " Cerca di essere conciso e diretto.")
