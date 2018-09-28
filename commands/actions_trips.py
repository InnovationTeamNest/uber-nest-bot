# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import separate_callback_data, create_callback_data as ccd


def trips_handler(bot, update):
    mode = separate_callback_data(update.callback_query.data)[1]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    log.debug("Mode entered: " + mode)
    if mode == "NEW_TRIP":
        keyboard = [
            [InlineKeyboardButton(common.direction_name[i], callback_data=ccd("NEWTRIP", common.direction_generic[i]))
             for i in range(0, len(common.direction_name), 1)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Vuoi aggiungere un viaggio verso il NEST o Povo? Ricorda che puoi aggiungere"
                              " un solo viaggio al giorno per direzione. Eventuali viaggi già presenti"
                              " verranno sovrascritti, passeggeri compresi.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "EDIT_TRIP":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]
        trip = secret_data.groups[direction][day][chat_id]

        keyboard = [
            [InlineKeyboardButton("Modifica l'ora", callback_data=ccd("TRIPS", "EDIT_TRIP_HOUR", direction, day))],
            [InlineKeyboardButton("Modifica i passeggeri", callback_data=ccd("TRIPS", "EDIT_USER", direction, day))],
            [InlineKeyboardButton("Cancella il viaggio", callback_data=ccd("TRIPS", "REMOVE_TRIP", direction, day))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
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
    elif mode == "EDIT_TRIP_HOUR":  # Inserimento dell'ora
        direction, day = separate_callback_data(update.callback_query.data)[2:4]

        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("TRIPS", "EDIT_TRIP_MINUTES", direction, day, i))
             for i in range(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=ccd("TRIPS", "EDIT_TRIP_MINUTES", direction, day, i))
             for i in range(14, 21, 1)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "EDIT_TRIP_MINUTES":  # Inserimento dei minuti
        direction, day, hour = separate_callback_data(update.callback_query.data)[2:5]

        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2),
                                  callback_data=ccd("TRIPS", "CONFIRM_EDIT_TRIP", direction, day, hour, i))
             for i in range(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=ccd("TRIPS", "CONFIRM_EDIT_TRIP", direction, day, hour, i))
             for i in range(30, 60, 5)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli i minuti di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "CONFIRM_EDIT_TRIP":
        direction, day, hour, minute = separate_callback_data(update.callback_query.data)[2:6]
        time = hour.zfill(2) + ":" + minute.zfill(2)

        trip = secret_data.groups[direction][unicode(day)][unicode(chat_id)]

        trip["Time"] = str(time)

        for user_group in trip["Permanent"], trip["Temporary"]:
            for user in user_group:
                bot.send_message(chat_id=user,
                                 text=secret_data.users[chat_id]["Name"] + " ha spostato l'orario del viaggio di "
                                      + day + common.direction_to_name(direction) + " alle " + str(time) + ".")

        bot.send_message(chat_id=chat_id, text="Nuovo orario di partenza:\n"
                                               + day + " alle "
                                               + str(time) + " " + common.direction_to_name(direction))
    elif mode == "EDIT_USER":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]
        permanent_users = secret_data.groups[direction][day][chat_id]["Permanent"]
        temporary_users = secret_data.groups[direction][day][chat_id]["Temporary"]

        keyboard = [
            [InlineKeyboardButton(secret_data.users[user]["Name"] + " - Permanente",
                                  callback_data=ccd("TRIPS", "REMOVE_USER", direction, day, user, "Permanent"))
             for user in permanent_users],
            [InlineKeyboardButton(secret_data.users[user]["Name"] + " - Temporaneo",
                                  callback_data=ccd("TRIPS", "REMOVE_USER", direction, day, user, "Temporary"))
             for user in temporary_users],
            [InlineKeyboardButton("Nuovo passeggero", callback_data=ccd("TRIPS", "ADD_USER", direction, day))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Clicca su un passeggero per rimuoverlo"
                                               + " dal tuo viaggio, oppure aggiungine uno"
                                               + " manualmente",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "ADD_USER":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]
        keyboard = []

        for user in secret_data.users:
            if user != chat_id:
                keyboard.append([InlineKeyboardButton(secret_data.users[user]["Name"],
                                                      callback_data=ccd("TRIPS", "MODE_ADD_USER", direction, day,
                                                                        user))])
        keyboard = [
            keyboard,
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Seleziona un passeggero da aggiungere al tuo viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "MODE_ADD_USER":
        direction, day, user = separate_callback_data(update.callback_query.data)[2:5]

        keyboard = [
            [
                [InlineKeyboardButton("Temporanea", callback_data=ccd("TRIPS", "CONFIRM_ADD_USER",
                                                                      direction, day, user, "Temporary"))],
                [InlineKeyboardButton("Permanente", callback_data=ccd("TRIPS", "CONFIRM_ADD_USER",
                                                                      direction, day, user, "Permanent"))]
            ],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "ADD_USER", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Scegli la modalità di prenotazione.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "CONFIRM_ADD_USER":
        direction, day, user, mode = separate_callback_data(update.callback_query.data)[2:6]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        trip = secret_data.groups[direction][day][chat_id]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secret_data.drivers[chat_id]["Slots"]

        if occupied_slots >= total_slots:
            bot.send_message(chat_id=chat_id, text="Temo che il tuo amico dovrà andare a piedi, i posti sono finiti.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        elif str(user) in trip["Temporary"] or str(user) in trip["Permanent"]:
            bot.send_message(chat_id=chat_id, text="Questa persona si è già prenotata in questo viaggio!",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            trip[mode].append(str(user))
            bot.send_message(chat_id=chat_id,
                             text="Prenotazione completata. Dati del viaggio:"
                                  + "\n\n👤: " + str(secret_data.users[user]["Name"])
                                  + "\n🗓: " + day
                                  + "\n🕓: " + trip["Time"]
                                  + "\n➡: " + common.direction_to_name(direction)
                                  + "\n🔁: " + common.localize_mode(mode),
                             reply_markup=InlineKeyboardMarkup(keyboard))
            bot.send_message(chat_id=user,
                             text=str(secret_data.users[chat_id]["Name"])
                                  + "ha effettuato una nuova prenotazione a tuo nome nel suo viaggio: "
                                  + "\n🗓: " + day
                                  + "\n🕓: " + trip["Time"]
                                  + "\n➡: " + common.direction_to_name(direction)
                                  + "\n🔁: " + common.localize_mode(mode))
    elif mode == "REMOVE_USER":
        direction, day, user, mode = separate_callback_data(update.callback_query.data)[2:6]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CONFIRM_REMOVE_USER", direction, day, user, mode)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler rimuovere questo passeggero?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "CONFIRM_REMOVE_USER":
        direction, day, user, mode = separate_callback_data(update.callback_query.data)[2:6]
        secret_data.groups[direction][day][chat_id][mode].remove(user)
        bot.send_message(chat_id=chat_id, text="Passeggero rimosso con successo.")
        bot.send_message(chat_id=user,
                         text=secret_data.users[chat_id]["Name"] + " ti ha rimosso dal viaggio di "
                              + day + " alle " + common.get_trip_time(chat_id, day, direction)
                              + common.direction_to_name(direction))
    elif mode == "REMOVE_TRIP":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CONFIRM_REMOVE_TRIP", direction, day)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif mode == "CONFIRM_REMOVE_TRIP":
        direction, day = separate_callback_data(update.callback_query.data)[2:4]
        del secret_data.groups[direction][day][chat_id]
        bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.")
