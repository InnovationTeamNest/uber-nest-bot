# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import unicode_literals

import logging as log
import math

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import separate_callback_data, create_callback_data as ccd


def trips_handler(bot, update):
    """Metodo gestore delle chiamate indirizzate da "TRIPS", sottomenu di /me"""
    data = separate_callback_data(update.callback_query.data)
    action = data[1]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    log.debug("Mode entered: " + action)
    if action == "NEW_TRIP":  # Chiamata sul bottone "Nuovo viaggio"
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
    elif action == "EDIT_TRIP":  # Chiamata sul bottone di un certo viaggio già presente
        direction, day = data[2:4]
        trip = secret_data.groups[direction][day][chat_id]

        keyboard = [
            [InlineKeyboardButton("Modifica l'ora", callback_data=ccd("TRIPS", "EDIT_TRIP_HOUR", direction, day))],
            [InlineKeyboardButton("Modifica i passeggeri",
                                  callback_data=ccd("TRIPS", "EDIT_PASSENGERS", direction, day))],
            [InlineKeyboardButton("Cancella il viaggio", callback_data=ccd("TRIPS", "REMOVE_TRIP", direction, day))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Viaggio selezionato: \n"
                              + "\nGiorno: " + day
                              + "\nDirezione: " + common.direction_to_name(direction)
                              + "\nOrario: " + trip["Time"]
                              + "\nPasseggeri temporanei: " + ",".join(secret_data.users[user]["Name"]
                                                                       for user in trip["Temporary"])
                              + "\nPasseggeri permanenti: " + ",".join(secret_data.users[user]["Name"]
                                                                       for user in trip["Permanent"])
                              + "\n\nCosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "EDIT_TRIP_HOUR":  # Inserimento dell'ora
        direction, day = data[2:4]

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
    elif action == "EDIT_TRIP_MINUTES":  # Inserimento dei minuti
        direction, day, hour = data[2:5]

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
    elif action == "CONFIRM_EDIT_TRIP":
        direction, day, hour, minute = data[2:6]
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
    # Comando chiamato una volta premuto il bottone della persona da prenotare
    elif action == "EDIT_PASSENGERS":
        direction, day = data[2:4]
        permanent_users = secret_data.groups[direction][day][chat_id]["Permanent"]
        temporary_users = secret_data.groups[direction][day][chat_id]["Temporary"]

        keyboard = [
            [InlineKeyboardButton(secret_data.users[user]["Name"] + " - Permanente",
                                  callback_data=ccd("TRIPS", "REMOVE_PASSENGER", direction, day, user, "Permanent"))
             for user in permanent_users],
            [InlineKeyboardButton(secret_data.users[user]["Name"] + " - Temporaneo",
                                  callback_data=ccd("TRIPS", "REMOVE_PASSENGER", direction, day, user, "Temporary"))
             for user in temporary_users],
            [InlineKeyboardButton("Nuovo passeggero",
                                  callback_data=ccd("TRIPS", "ADD_PASSENGER", direction, day, "0"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Clicca su un passeggero per rimuoverlo"
                                               + " dal tuo viaggio, oppure aggiungine uno"
                                               + " manualmente.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato dalla vista viaggio per aggiungere un passeggero
    elif action == "ADD_PASSENGER":
        direction, day, page = data[2:5]

        keyboard = []
        page = int(page)
        users = sorted([(secret_data.users[user]["Name"], user) for user in secret_data.users if user != chat_id])
        # Resituisce una lista di tuple del tipo (Nome, ID)

        for index in range(common.PAGE_SIZE * page, common.PAGE_SIZE * (page + 1), 1):
            try:
                keyboard.append([InlineKeyboardButton(users[index][0],
                                                      callback_data=ccd("TRIPS", "ADD_PASSENGER_MODE", direction, day,
                                                                        users[index][1]))])
            except IndexError:
                break

        # Aggiungo un bottone per ogni pagina, in quanto la lista è troppo grande
        page_buttons = []
        for index in range(0, int(math.ceil(len(users) / common.PAGE_SIZE)), 1):
            if index == page:
                text = "☑"
            else:
                text = str(index + 1)
            page_buttons.append(InlineKeyboardButton(text,
                                                     callback_data=ccd("TRIPS", "ADD_PASSENGER", direction, day,
                                                                       index)))
        keyboard.append(page_buttons)

        keyboard.append([InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))])
        keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])
        bot.send_message(chat_id=chat_id,
                         text="Seleziona un passeggero da aggiungere al tuo viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato una volta premuto il bottone della persona da prenotare
    elif action == "ADD_PASSENGER_MODE":
        direction, day, user = data[2:5]

        keyboard = [
            [InlineKeyboardButton("Temporanea", callback_data=ccd("TRIPS", "CONFIRM_ADD_PASSENGER",
                                                                  direction, day, user, "Temporary"))],
            [InlineKeyboardButton("Permanente", callback_data=ccd("TRIPS", "CONFIRM_ADD_PASSENGER",
                                                                  direction, day, user, "Permanent"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "ADD_PASSENGER", direction, day, "0"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Scegli la modalità di prenotazione.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato una volta premuto il bottone della persona da prenotare e scelta la modalità
    elif action == "CONFIRM_ADD_PASSENGER":
        direction, day, user, mode = data[2:6]

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
                                  + " ha effettuato una nuova prenotazione a tuo nome nel suo viaggio: "
                                  + "\n🗓: " + day
                                  + "\n🕓: " + trip["Time"]
                                  + "\n➡: " + common.direction_to_name(direction)
                                  + "\n🔁: " + common.localize_mode(mode))
    # Comando chiamato in seguito a pressione del bottone contenente un utente di un viaggio
    elif action == "REMOVE_PASSENGER":
        direction, day, user, mode = data[2:6]

        keyboard = [
            [InlineKeyboardButton("Sì",
                                  callback_data=ccd("TRIPS", "CONFIRM_REMOVE_PASSENGER", direction, day, user, mode)),
             InlineKeyboardButton("No", caallback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler rimuovere questo passeggero?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato in caso di rispsota positiva al precedente comando
    elif action == "CONFIRM_REMOVE_PASSENGER":
        direction, day, user, mode = data[2:6]
        secret_data.groups[direction][day][chat_id][mode].remove(user)
        bot.send_message(chat_id=chat_id, text="Passeggero rimosso con successo.")
        bot.send_message(chat_id=user,
                         text=secret_data.users[chat_id]["Name"] + " ti ha rimosso dal viaggio di "
                              + day + " alle " + secret_data.groups[direction][day][chat_id]["Time"]
                              + " " + common.direction_to_name(direction))
    # Comando chiamato quando si clicca su "Rimuovi viaggio" nella vista viaggio
    elif action == "REMOVE_TRIP":
        direction, day = data[2:4]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CONFIRM_REMOVE_TRIP", direction, day)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato in caso di risposta positiva al precedente comando
    elif action == "CONFIRM_REMOVE_TRIP":
        direction, day = data[2:4]
        del secret_data.groups[direction][day][chat_id]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
