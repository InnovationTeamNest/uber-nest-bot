# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import logging as log

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import create_callback_data as ccd, separate_callback_data
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
                         text="Viaggi (clicca su un viaggio per modificarlo):",
                         reply_markup=trips_keyboard(update))
    elif mode == "DRIVER":
        if str(chat_id) in secret_data.drivers:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=ccd("ME", "DELETEDRIVER")),
                 InlineKeyboardButton("No", callback_data=ccd("CANCEL"))]]
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler confermare la tua rimozione dalla"
                                  " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                  " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                  " completo di tutte le prenotazioni.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=ccd("ME", "SLOTSDRIVER")),
                 InlineKeyboardButton("No", callback_data=ccd("CANCEL"))]]
            bot.send_message(chat_id=chat_id,
                             text="Una volta finalizzata l'iscrizione come autista, potrai gestire i tuoi"
                                  " viaggi direttamente da questo bot. Contatta un membro del direttivo di"
                                  " UberNEST per ulteriori informazioni.\n\n"
                                  "Sei sicuro di voler diventare un autista di UberNEST?",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "REMOVAL":
        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("ME", "CONFIRMREMOVAL")),
             InlineKeyboardButton("No", callback_data=ccd("CANCEL"))]]

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
    elif mode == "SLOTSDRIVER":
        # Inserisco 5 bottoni per i posti con la list comprehension
        keyboard = [[InlineKeyboardButton(str(i), callback_data=ccd("ME", "CONFIRMDRIVER", str(i)))
                     for i in range(1, 6, 1)],
                    [InlineKeyboardButton("Annulla", callback_data=ccd("CANCEL"))]]
        bot.send_message(chat_id=chat_id,
                         text="Inserisci il numero di posti disponibili nella tua macchina, autista escluso.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
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
            [InlineKeyboardButton(common.direction_name[i], callback_data=ccd("NEWTRIP", common.direction_generic[i]))
             for i in range(0, len(common.direction_name), 1)],
            [InlineKeyboardButton("Annulla", callback_data=ccd("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Vuoi aggiungere un viaggio verso il NEST o Povo? Ricorda che puoi aggiungere"
                              " un solo viaggio al giorno per direzione. Eventuali viaggi già presenti"
                              " verranno sovrascritti, passeggeri compresi.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "EDIT":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]
        trip = secret_data.groups[direction][day][chat_id]

        keyboard = [
            [InlineKeyboardButton("Modificare l'ora", callback_data=ccd("TRIPS", "EDITHOUR", direction, day))],
            [InlineKeyboardButton("Rimuovere un passeggero", callback_data=ccd("TRIPS", "EDITUSER", direction, day))],
            [InlineKeyboardButton("Cancellare il viaggio", callback_data=ccd("TRIPS", "DELETE", direction, day))],
            [InlineKeyboardButton("Tornare alla lista dei viaggi", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Uscire", callback_data=ccd("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Viaggio selezionato: \n"
                              + "\nGiorno: " + day
                              + "\nDirezione: " + common.direction_to_name(direction)
                              + "\nOrario: " + common.get_trip_time(chat_id, day, direction)
                              + "\nPasseggeri temporanei: " + ",".join(secret_data.users[user]["Name"]
                                                                       for user in trip["Temporary"])
                              + "\nPasseggeri permanenti: " + ",".join(secret_data.users[user]["Name"]
                                                                       for user in trip["Permanent"])
                              + "\n\nCosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "EDITHOUR":  # Inserimento dell'ora
        direction, day = separate_callback_data(update.callback_query.data)[2:4]

        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("TRIPS", "EDITMINUTES", direction, day, i))
             for i in range(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=ccd("TRIPS", "EDITMINUTES", direction, day, i))
             for i in range(14, 21, 1)],
            [InlineKeyboardButton("Torna alla visualizzazione viaggio",
                                  callback_data=ccd("TRIPS", "EDIT", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("CANCEL"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "EDITMINUTES":  # Inserimento dei minuti
        direction, day, hour = separate_callback_data(update.callback_query.data)[2:5]

        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("TRIPS", "CONFIRMEDIT", direction, day, hour, i))
             for i in range(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=ccd("TRIPS", "CONFIRMEDIT", direction, day, hour, i))
             for i in range(30, 60, 5)],
            [InlineKeyboardButton("Torna alla visualizzazione viaggio",
                                  callback_data=ccd("TRIPS", "EDIT", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("CANCEL"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli i minuti di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "CONFIRMEDIT":
        direction, day, hour, minute = separate_callback_data(update.callback_query.data)[2:6]
        time = hour.zfill(2) + ":" + minute.zfill(2)

        secret_data.groups[direction][unicode(day)][unicode(chat_id)]["Time"] = str(time)
        bot.send_message(chat_id=chat_id, text="Nuovo orario di partenza:\n"
                                               + day + " alle "
                                               + str(time) + common.direction_to_name(direction))
    elif mode == "EDITUSER":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]
        permanent_users = secret_data.groups[direction][day][chat_id]["Permanent"]
        temporary_users = secret_data.groups[direction][day][chat_id]["Temporary"]

        keyboard = [
            [InlineKeyboardButton(secret_data.users[user]["Name"] + " - Permanente",
                                  callback_data=ccd("TRIPS", "REMOVEUSER", direction, day, user, "Permanent"))
             for user in permanent_users],
            [InlineKeyboardButton(secret_data.users[user]["Name"] + " - Temporaneo",
                                  callback_data=ccd("TRIPS", "REMOVEUSER", direction, day, user, "Temporary"))
             for user in temporary_users],
            [InlineKeyboardButton("Torna alla visualizzazione viaggio",
                                  callback_data=ccd("TRIPS", "EDIT", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("CANCEL"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli un passeggero da rimuovere dal tuo viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "REMOVEUSER":
        direction, day, user, mode = separate_callback_data(update.callback_query.data)[2:6]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CONFIRMREMOVEUSER", direction, day, user, mode)),
             InlineKeyboardButton("No", callback_data=ccd("CANCEL"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler rimuovere questo passeggero?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "CONFIRMREMOVEUSER":
        direction, day, user, mode = separate_callback_data(update.callback_query.data)[2:6]
        secret_data.groups[direction][day][chat_id][mode].remove(user)
        bot.send_message(chat_id=chat_id, text="Passeggero rimosso con successo.")
        bot.send_message(chat_id=user,
                         text=secret_data.users[chat_id]["Name"]
                              + " ti ha rimosso dal viaggio di "
                              + day + " alle " + common.get_trip_time(chat_id, day, direction)
                              + common.direction_to_name(direction))
    elif mode == "DELETE":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CONFIRMDELETION", direction, day)),
             InlineKeyboardButton("No", callback_data=ccd("CANCEL"))]
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
            keyboard.append(InlineKeyboardButton(day[:2], callback_data=ccd("NEWTRIP", day, *data)))
        # Aggiungo il pulsante annulla
        keyboard = [keyboard,
                    [InlineKeyboardButton("Annulla", callback_data=ccd("CANCEL"))]]

        bot.send_message(chat_id=chat_id, text="Scegli il giorno della settimana del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 2:  # Inserimento dell'ora
        keyboard = [  # Ordine: ora, giorno, direzione
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(14, 21, 1)],
            [InlineKeyboardButton("Annulla", callback_data=ccd("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio. ",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 3:  # Inserimento dei minuti
        keyboard = [  # Ordine: minuti, ora, giorno, direzione
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=ccd("NEWTRIP", str(i), *data))
             for i in range(30, 60, 5)],
            [InlineKeyboardButton("Annulla", callback_data=ccd("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Scegli i minuti di partenza del viaggio.",
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
